import sys
import os
import click
from shutil import copy2
from typing import List, Callable, Dict, Optional, Tuple

class FileDesc():
    def __init__(self, root: str, file_name: str):
        self.root = root
        self.filename = file_name
        self.filesize = 0
        self.full = root + '/' + file_name

    def __str__(self):
        return '{} {}'.format(self.filename, self.root)

    def __repr__(self):
        return self.__str__()


def recursive_full_path(directory: str) -> List[FileDesc]:
    ret: List[FileDesc] = []

    for root, dirs, files in os.walk(os.path.abspath(directory)):
        for f in files:
            ret.append(FileDesc(root, f))
    return ret


def comparison(source_list: List[FileDesc],
               destination_list: List[FileDesc],
               func: Callable[[FileDesc, Dict[str, FileDesc]], bool]) -> List[FileDesc]:
    destination = {}
    return_list = []

    for d in destination_list:
        destination[d.filename] = d

    for source in source_list:
        ret = func(source, destination)
        if ret:
            return_list.append(source)

    return return_list


def directory_comparison(source_directory: str,
                         dest_directory: str,
                         func: Callable[[FileDesc, Dict[str, FileDesc]], bool]) -> List[FileDesc]:
    source_list = recursive_full_path(source_directory)
    destination_list = recursive_full_path(dest_directory)

    return comparison(source_list,
                      destination_list,
                      func)


def get_missing_files(source_directory: str, dest_directory: str) -> List[FileDesc]:
    return directory_comparison(source_directory,
                                dest_directory,
                                lambda source_f, dest: source_f.filename not in dest)


def get_duplicate_files(source_directory: str, dest_directory: str) -> List[FileDesc]:
    return directory_comparison(source_directory,
                                dest_directory,
                                lambda source_f, dest: source_f.filename in dest)


def get_duplicate_different_size(source_directory: str, dest_directory: str) -> List[FileDesc]:
    duplicates = get_duplicate_files(source_directory, dest_directory)

    different_dup = []
    for dup in duplicates:
        try:
            source_size = os.path.getsize(dup.root + '/' + dup.filename)
            dest_size = os.path.getsize(dest_directory + '/' + dup.filename)
            if source_size != dest_size:
                different_dup.append(dup)
        except OSError as e:
            continue

    return different_dup


def get_duplicate_same_size(source_directory: str, dest_directory: str) -> List[FileDesc]:
    duplicates = get_duplicate_files(source_directory, dest_directory)

    exact_dup = []
    for dup in duplicates:
        try:
            source_size = os.path.getsize(dup.root + '/' + dup.filename)
            dest_size = os.path.getsize(dest_directory + '/' + dup.filename)
            if source_size == dest_size:
                exact_dup.append(dup)
        except OSError as e:
            continue

    return exact_dup


def copy_source_recursive_to_destination(source_directory: str, dest_directory: str, test: bool = False):
    extensions = ['.jpg', '.png', '.jpeg', '.gif', '.avi', '.mov', '.mpg', '.mp4', '.cr2']

    def is_extension(f: FileDesc):
        lower = f.filename.lower()
        for e in extensions:
            if lower.endswith(e):
                return True
        return False

    logfile = open('sync_directory.log', 'a')

    # copy missing files first
    missing_files = get_missing_files(source_directory, dest_directory)
    missing_files = list(filter(is_extension, missing_files))
    for f in missing_files:
        print('cp {} to {}'.format(f.full, dest_directory))
        if not test:
            copy2(f.full, dest_directory)
            logfile.write('{},{}\n'.format(f.full, dest_directory))

    dupes_different_size = get_duplicate_different_size(source_directory, dest_directory)
    dupes_different_size = list(filter(is_extension, dupes_different_size))
    for f in dupes_different_size:
        diff_filename = f.filename[:f.filename.index('.')] + ' (1)' + f.filename[f.filename.index('.'):]
        print('duplicate filename but different file size: cp {} to {}'
              .format(f.full, dest_directory + '/' + diff_filename))
        if not test:
            copy2(f.full, dest_directory + '/' + diff_filename)
            logfile.write('{},{}\n'.format(f.full, dest_directory + '/' + diff_filename))

    dupes_same_size = get_duplicate_same_size(source_directory, dest_directory)
    dupes_same_size = list(filter(is_extension, dupes_same_size))
    for f in dupes_same_size:
        print('skipping duplicate (same file size): {}'.format(f))


@click.command()
@click.option('--source_dir', required=True, help='Source directory of images to import')
@click.option('--destination_dir', required=True, help='Destination directory of images')
@click.option('--test_run', is_flag=True, help='Show actions without importing files')
def main(source_dir: str, destination_dir: str, test_run: bool):
    copy_source_recursive_to_destination(source_dir, destination_dir, test_run)


if __name__ == '__main__':
    main()
