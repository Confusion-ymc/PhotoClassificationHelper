from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter.messagebox import *
import threading

from utils import *


def loading(finish, count):
    canvas.coords(fill_line, (0, 0, finish / count * canvas_w, 30))
    start_btn['text'] = str(round(finish / count * 100, 1)) + "%"
    root.update()


def thread_t(folder_helper: FolderUtils):
    the_same_file = []
    file_count = folder_helper.count_for_detail_photos()
    finish = 0

    for file_path_ in folder_helper.scan_folder(folder_helper.from_root_path):
        finish += 1
        new_image = ImageInfo(file_path_)
        file_md5, folder_id_by_date, photo_name = new_image.read_info()
        if file_md5 not in folder_helper.md5_dic:
            # 如果读取到日期信息
            folder_by_date = folder_id_by_date
            if folder_by_date == '未知时间' and use_modify_time_check_var.get():
                # 如果用户选择了使用文件创建时间
                folder_by_date = new_image.modify_time
            # 创建文件夹
            FolderUtils.mkdir(
                os.path.join(folder_helper.to_root_path, folder_helper.dir_map.get(folder_by_date, folder_by_date)))
            if use_location_folder_name_var.get():
                # 根据city重命名文件夹
                address, city = new_image.get_position_by_api()
                folder_helper.rename_dir_by_city(folder_by_date, city)
            else:
                folder_helper.dir_map[folder_by_date] = folder_by_date
            # 开始移动文件夹
            new_file_path = os.path.join(folder_helper.to_root_path, folder_helper.dir_map[folder_by_date], photo_name)
            # 移动文件并显示信息
            set_status_text(FolderUtils.move_file(file_path_, new_file_path))
            folder_helper.md5_dic[file_md5] = [folder_by_date, photo_name]
        else:
            the_same_file.append([file_path_, file_md5])
            msg = '跳过: {}, 存在文件:{}(文件夹名字可能已被修改)'.format(file_path_, os.path.join(folder_helper.to_root_path,
                                                                                 folder_helper.md5_dic[file_md5][0],
                                                                                 photo_name))
            print(msg)
            set_status_text(msg)
        loading(finish, file_count)
    print('找到的相同的文件:')

    for i in the_same_file:
        folder_id_by_date, photo_name = folder_helper.md5_dic[i[1]]
        exist_file_path = os.path.join(folder_helper.to_root_path, folder_helper.dir_map[folder_id_by_date], photo_name)
        msg = '相同文件: {}  =====>  {}'.format(i[0], exist_file_path)
        print(msg)
        set_status_text(msg)
    showinfo('提示', '完成!')
    from_btn['state'] = 'normal'
    to_btn['state'] = 'normal'
    start_btn['state'] = 'normal'
    start_btn['text'] = '   开始   '
    set_status_text('全部完成!')


def run(from_folder, move_to_folder):
    new_folder_helper = FolderUtils(from_folder, move_to_folder)
    # 判断移动的文件夹是否为空
    if not new_folder_helper.is_empty_dir(move_to_folder):
        showinfo('提示', '输出文件夹请选择空文件夹!')
        return
    threading.Thread(target=thread_t, args=(new_folder_helper,), daemon=True).start()
    from_btn['state'] = 'disabled'
    to_btn['state'] = 'disabled'
    start_btn['state'] = 'disabled'
    start_btn['text'] = '运行中'


def selectPath(path):
    path_ = askdirectory()
    path.set(path_)


def set_status_text(text):
    status_text["text"] = '状态: ' + text


if __name__ == '__main__':
    root = Tk()
    root.geometry('395x200')
    root.maxsize('395', '200')
    # root.resizable(0, 0)
    root.title('照片分类助手')
    from_path = StringVar()
    to_path = StringVar()
    use_modify_time_check_var = BooleanVar()
    use_location_folder_name_var = BooleanVar()

    Label(root, text="输入路径:").grid(row=0, column=0, sticky=W)
    from_path_entry = Entry(root, textvariable=from_path)
    from_path_entry.grid(row=0, column=1, sticky=W)
    from_btn = Button(root, text="路径选择", command=lambda: selectPath(from_path))
    from_btn.grid(row=0, column=2, sticky=E)

    Label(root, text="保存路径:").grid(row=1, column=0, sticky=W)
    to_path_entry = Entry(root, textvariable=to_path)
    to_path_entry.grid(row=1, column=1, sticky=W)
    to_btn = Button(root, text="路径选择", command=lambda: selectPath(to_path))
    to_btn.grid(row=1, column=2, sticky=E)
    # 没有拍摄时间使用修改时间
    use_modify_time_check = Checkbutton(root, text="没有拍摄时间使用修改时间", variable=use_modify_time_check_var)
    use_modify_time_check.grid(row=2, column=0, columnspan=2, sticky=W)
    # 统计图片地址信息命名文件夹
    use_location_folder_name = Checkbutton(root, text="统计图片地址信息命名文件夹", variable=use_location_folder_name_var)
    use_location_folder_name.grid(row=3, column=0, columnspan=2, sticky=W)

    start_btn = Button(root, text="   开始   ", command=lambda: run(from_path_entry.get(), to_path_entry.get()))
    start_btn.grid(row=3, column=2, sticky=E)

    # 进度条
    # 创建一个背景色为白色的矩形
    canvas_h = 15
    canvas_w = 361
    canvas = Canvas(root, width=canvas_w, height=canvas_h, bg="white")
    # 创建一个矩形外边框（距离左边，距离顶部，矩形宽度，矩形高度），线型宽度，颜色
    out_line = canvas.create_rectangle(2, 2, canvas_w, canvas_h, width=1, outline="black")
    canvas.grid(row=5, column=0, columnspan=3, sticky=SW, pady=30)

    status_text = Label(root, text='状态: 准备就绪!', anchor='nw', width=50)
    status_text.grid(row=5, column=0, columnspan=3, sticky=SW, pady=10)
    fill_line = canvas.create_rectangle(2, 2, 0, 27, width=0, fill="green")

    root.mainloop()
