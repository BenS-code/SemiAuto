import time
from pathlib import Path


def create_dir(sn, main_path, process):
    # create folder

    date_string = time.strftime("%Y-%m-%d")
    time_string = time.strftime("%H-%M-%S")

    path_str = main_path + '/' + process + '/'
    unit_folder = Path(path_str)
    unit_folder.mkdir(exist_ok=True)
    path_str = main_path + '/' + process + '/' + sn
    unit_folder = Path(path_str)
    unit_folder.mkdir(exist_ok=True)
    path_str = main_path + '/' + process + '/' + sn + '/' + date_string
    unit_folder = Path(path_str)
    unit_folder.mkdir(exist_ok=True)
    path_str = main_path + '/' + process + '/' + sn + '/' + date_string + '/' + time_string
    unit_folder = Path(path_str)
    unit_folder.mkdir(exist_ok=True)

    return path_str
