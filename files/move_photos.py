import os
import shutil
import time

from exifread import process_file


def get_created_date(file_path):
    with open(file_path, 'rb') as img_file:
        exif = process_file(img_file, details=False, stop_tag='DateTimeOriginal')
        created = exif.get('EXIF DateTimeOriginal')
        if created is None:
            return time.gmtime(os.path.getmtime(file_path))  # fall back to file modification date
        created_str = str(created)
        # both date formats seems to be present in jpeg files, 2018-12-01 and 2018:12:01
        if created_str.find('-') > 0:
            return time.strptime(created_str, '%Y-%m-%d %H:%M:%S')
        else:
            return time.strptime(created_str, '%Y:%m:%d %H:%M:%S')


def get_target_path(suffix, file_path):
    created = get_created_date(file_path)
    return suffix + '/' + time.strftime('%Y/%m/%Y-%m-%d-', created) + os.path.basename(file_path)


source = "/mnt/backup"
target = "/mnt/photo"
skipped = 0
copied = 0

for dir_path, dir_names, file_names in os.walk(source):
    for file_name in file_names:
        if file_name.lower().endswith(('jpg', 'jpeg', 'raw', 'mpg', 'mpeg',  'mp2', 'm2v', 'mp4', 'avi', 'mov',
                                       'qt')):
            source_path = os.path.join(dir_path, file_name)
            target_path = get_target_path(target, source_path)
            if os.path.exists(target_path):
                skipped = skipped + 1
            else:
                print(target_path)
                target_path_dir = os.path.dirname(target_path)
                if not os.path.exists(target_path_dir):
                    os.makedirs(target_path_dir)
                shutil.copy2(source_path, target_path)
                copied = copied + 1
print('skipped existing files: ' + str(skipped))
print('copied new files: ' + str(copied))
