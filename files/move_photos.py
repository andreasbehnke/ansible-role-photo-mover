#!/usr/bin/env python3
import os
import shutil
import sys
import time

from exifread import process_file
from datetime import datetime

def get_created_date(file_path):
    with open(file_path, 'rb') as img_file:
        exif = process_file(img_file, details=False, stop_tag='DateTimeOriginal')
        created = exif.get('EXIF DateTimeOriginal')
        if created is None or len(str(created)) != 19:  # 2018-12-01 12:34:56
            return time.gmtime(os.path.getmtime(file_path))  # fall back to file modification date
        created_str = str(created)
        # both date formats seems to be present in jpeg files, 2018-12-01 and 2018:12:01
        if created_str.find('-') > 0:
            return time.strptime(created_str, '%Y-%m-%d %H:%M:%S')
        else:
            return time.strptime(created_str, '%Y:%m:%d %H:%M:%S')


def get_target_path(suffix, pattern, file_path):
    created = get_created_date(file_path)
    time_pattern = pattern.replace('%f', os.path.basename(file_path))
    return suffix + '/' + time.strftime(time_pattern, created)

def ensure_directories(target_path):
    target_path_dir = os.path.dirname(target_path)
    if not os.path.exists(target_path_dir):
        os.makedirs(target_path_dir)

def move_file_if_not_exists(debug, source_path, target_path):
    if os.path.exists(target_path):
        return False
    else:
        if debug:
            print('cp ' + target_path)
        ensure_directories(target_path)
        shutil.copy2(source_path, target_path)
        return True

def link_file(debug, source_path, target_path, trash_bin_path):
    if (os.path.exists(target_path)):
        if (not os.path.samefile(source_path, target_path)):
            # remove duplicate file by creating hard link
            if debug:
                print('ln existing ' + target_path)
            # create backup for security reasons
            if (not os.path.exists(os.path.join(trash_bin_path, os.path.basename(target_path)))):
                shutil.move(target_path, trash_bin_path) # create backup
            else:
                os.remove(target_path) # delete existing
            os.link(source_path, target_path) #  and link with source
            return True
        else:
            return False
    else :
        if debug:
            print('ln ' + target_path)
        ensure_directories(target_path)
        os.link(source_path, target_path)
        return True
        
def move_files(sources, target, file_path_pattern, create_links = True, trash_bin_path_postfix = '/trash/'):
    skipped = 0
    copied = 0
    trash_bin_path = target + trash_bin_path_postfix

    for source in sources:
        for dir_path, _, file_names in os.walk(source):
            for file_name in file_names:
                if file_name.lower().endswith(('jpg', 'jpeg', 'raw', 'mpg', 'mpeg',  'mp2', 'm2v', 'mp4', 'avi', 'mov',
                                            'qt')):
                    source_path = os.path.join(dir_path, file_name)
                    target_path = get_target_path(target, file_path_pattern, source_path)
                    modified = False
                    if (create_links):
                        if not os.path.exists(trash_bin_path):
                            os.makedirs(trash_bin_path) # ensure trash bin exists
                        modified = link_file(False, source_path, target_path, trash_bin_path)
                    else:
                        modified = move_file_if_not_exists(False, source_path, target_path)
                    if modified:
                        copied = copied + 1
                    else:
                        skipped = skipped + 1
    print('skipped existing files: ' + str(skipped))
    print('copied new files: ' + str(copied))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: move_photos.py source_list_file target [file_path_pattern]")
        print("       source_list_file:  file containing source pathes, one per line")
        print("       target:  target path to move media files")
        print("       file_path_pattern:  file renaming pattern, defaults to '%Y/%m/%Y-%m-%d-%f'")
        exit()
    
    sources_file_path = sys.argv[1]
    target = sys.argv[2]
    file_path_pattern = '%Y/%m/%Y-%m-%d-%f'
    if (len(sys.argv) > 3):
        file_path_pattern = sys.argv[3]
    sources = []
    with open(sources_file_path) as sources_file:
        for line in sources_file:
            sources.append(line.strip())
    print('started at ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print('target: ' + target)
    print('sources: ' + str(sources))
    print('file_path_pattern: ' + file_path_pattern)
    move_files(sources, target, file_path_pattern)
