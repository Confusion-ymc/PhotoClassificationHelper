import datetime
import hashlib
import os
import shutil

import exifread
import requests
from GPSPhoto import gpsphoto


class ImageInfo:
    def __init__(self, file_path):
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
        self.create_time = str(raw_time).split(' ')[0].replace(':', '')[:6] if raw_time else '未知时间'
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
        self.dir_map = {}
        self.md5_dic = {}
        self.photo_count = 0
        self.from_root_path = from_root_path
        self.to_root_path = to_root_path

    @staticmethod
    def move_file(file_path, new_file_path):
        shutil.copyfile(file_path, new_file_path)  # 复制文件
        shutil.copystat(file_path, new_file_path)  # 复制信息
        if 'None' in new_file_path:
            print()
        print("copy %s -> %s" % (file_path, new_file_path))
        return "copy %s -> %s" % (file_path, new_file_path)

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

    def count_for_detail_photos(self):
        for i in self.scan_folder(self.from_root_path):
            self.photo_count += 1
        for file_path_ in self.scan_folder(self.to_root_path):
            file_md5, folder_by_date, photo_name = ImageInfo(file_path_).read_info()
            # 统计目标文件夹已经存在的图片信息
            if file_md5 not in self.md5_dic:
                self.md5_dic[file_md5] = [folder_by_date, photo_name]
        return self.photo_count

    @staticmethod
    def is_empty_dir(dir_path):
        if not os.listdir(dir_path):
            return True
        else:
            return False

    @staticmethod
    def rename_dir(old_name, new_name):
        os.rename(old_name, new_name)

    def rename_dir_by_city(self, month_dir_name, city):
        temp_folder_name = self.dir_map.get(month_dir_name)
        cities = [month_dir_name]
        # 根据city重命名文件夹
        if not temp_folder_name:
            temp_folder_name = month_dir_name
        else:
            cities = temp_folder_name.split('-')
        if city and city not in cities:
            cities.append(city)
        ##### 结束 #####
        new_folder_name = '-'.join(cities)
        self.dir_map[month_dir_name] = new_folder_name
        FolderUtils.rename_dir(os.path.join(self.to_root_path, temp_folder_name),
                               os.path.join(self.to_root_path, new_folder_name))

    @staticmethod
    def mkdir(folder_path):
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
            return True
        else:
            # 如果目录存在则不创建，并提示目录已存在
            # print(path + ' 目录已存在')
            return False


if __name__ == '__main__':
    pass
