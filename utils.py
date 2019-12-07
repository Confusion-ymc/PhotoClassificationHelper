import datetime
import hashlib
import os
import re
import traceback
import shutil

import exifread
import requests
from GPSPhoto import gpsphoto


class ImageInfo:
    def __init__(self, file_path, use_modify_time):
        self.use_modify_time = use_modify_time
        self.path = file_path
        self.photo_name = os.path.split(file_path)[-1]
        self.modify_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y%m')
        self.url_get_position = 'https://restapi.amap.com/v3/geocode/regeo?output=JSON&location={}&key={}'
        self.api_key = 'f84cbb2dc078c087c6dc37b6ae74ab85'
        self.md5_code = None
        self.create_time = None
        self.city = None
        self.address = None

    def read_info(self):
        m = hashlib.md5()
        with open(self.path, 'rb') as f:
            tags = exifread.process_file(f)
            for line in f:
                m.update(line)
        md5code = m.hexdigest()
        raw_time = tags.get('EXIF DateTimeOriginal')
        self.create_time = str(raw_time).split(' ')[0].replace(':', '')[:6] if raw_time else (
            self.modify_time if self.use_modify_time else '未知时间')
        self.md5_code = md5code
        return md5code, self.create_time, self.photo_name

    def get_position_by_api(self):
        try:
            gps_info = gpsphoto.getGPSData(self.path)
            location = f"{gps_info.get('Longitude')},{gps_info.get('Latitude')}"
            resp = requests.get(self.url_get_position.format(location, self.api_key)).json()
            address = resp.get('regeocode').get('formatted_address')
            city = resp.get('regeocode').get('addressComponent').get('city')
            self.city = city
            self.address = address
            return address, city
        except Exception as err:
            return None, None


class FolderUtils:
    def __init__(self, from_root_path, to_root_path):
        self.dir_city_map = {}
        self.md5_dic = {}
        self.the_same_images = []
        self.photo_count = 0
        self.from_root_path = from_root_path
        self.to_root_path = to_root_path

    @staticmethod
    def scan_folder(folder_path):
        for file_path, sub_dirs, filenames in os.walk(folder_path):
            if filenames:
                for filename in filenames:
                    file_path_ = os.path.join(file_path, filename)
                    yield file_path_
                    # file_lst.append(os.path.join(file_path, filename))
            for sub_dir in sub_dirs:
                # 如果是目录，则递归调用该函数
                FolderUtils.scan_folder(sub_dir)

    def count_for_deal_with_photos(self):
        for i in self.scan_folder(self.from_root_path): self.photo_count += 1

    def add_photo_info_to_md5(self, img_obj: ImageInfo):
        if img_obj.md5_code not in self.md5_dic:
            self.md5_dic[img_obj.md5_code] = img_obj
            return True
        else:
            self.the_same_images.append([img_obj, self.md5_dic[img_obj.md5_code]])
            return False

    def scan_exist_photos(self, use_modify_time):
        # 统计目标文件夹已经存在的图片信息
        pattern = re.compile(r'^[0-9]{6}.*?')
        for file_path, sub_dirs, filenames in os.walk(self.to_root_path):
            for folder_ in sub_dirs:
                if str(folder_).endswith('-'):
                    continue
                result = pattern.findall(folder_)
                if not result:
                    continue
                else:
                    self.dir_city_map[result[0]] = set(folder_.split('-')[1:])
                    for photo_path in self.scan_folder(os.path.join(file_path, folder_)):
                        new_image = ImageInfo(photo_path, use_modify_time)
                        new_image.read_info()
                        if new_image.city:
                            self.dir_city_map[result[0]].add(new_image.city)
                        self.add_photo_info_to_md5(new_image)

    @staticmethod
    def is_empty_dir(dir_path):
        if not os.listdir(dir_path):
            return True
        else:
            return False

    @staticmethod
    def rename_dir(old_name, new_name):
        os.rename(old_name, new_name)

    def rename_dir_by_city(self):
        for date_folder, cities in self.dir_city_map.items():
            if cities:
                old_folder_path = os.path.join(self.to_root_path, date_folder)
                new_folder_path = os.path.join(self.to_root_path, '-'.join([date_folder, *cities]))
                FolderUtils.rename_dir(old_folder_path, new_folder_path)
                print('重命名文件夹 {} --> {}'.format(old_folder_path, new_folder_path))

    def mkdir(self, folder_path):
        # 去除首位空格
        path = folder_path.strip()
        # 去除尾部 \ 符号
        # path = path.rstrip("\\")
        # 判断路径是否存在
        is_exists = os.path.exists(path)
        # 判断结果
        if not is_exists:
            # 如果不存在则创建目录
            os.makedirs(path)
            # print(path + ' 创建成功')
            self.dir_city_map[os.path.split(folder_path)[-1]] = set()
            return True
        else:
            # 如果目录存在则不创建，并提示目录已存在
            # print(path + ' 目录已存在')
            return False

    def move_file(self, image_obj: ImageInfo):
        old_path = image_obj.path
        date_folder_path = os.path.join(self.to_root_path, image_obj.create_time)
        new_path = os.path.join(date_folder_path, image_obj.photo_name)
        # 先创建文件夹
        self.mkdir(date_folder_path)
        try:
            shutil.copyfile(old_path, new_path)  # 复制文件
            shutil.copystat(old_path, new_path)  # 复制信息
            if 'None' in new_path:
                print()
            print("copy %s -> %s" % (old_path, new_path))
            image_obj.path = new_path
            return "copy %s -> %s" % (old_path, new_path)
        except:
            print('处理失败：copy %s -> %s' % (old_path, new_path))
            print(traceback.format_exc())


if __name__ == '__main__':
    pass
