import sys
import typing
import PIL
import os
import numpy as np
import shutil
import datetime as dt
import click
import logging
import coloredlogs
from PIL import Image, ImageFile
from typing import List, Tuple, Dict


def process(img_directory: str, trash_directory: str) -> None:
    MIN_SIZE = (400, 400)
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    source_files = os.listdir(img_directory)

    if os.path.exists('trim.log'):
        os.remove('trim.log')

    with open('trim.log', 'w') as log_file:
        for f in source_files:
            try:
                im = Image.open(img_directory + '/' + f)
                if im.size[0] <= MIN_SIZE[0] and im.size[1] <= MIN_SIZE[1]:
                    logging.info('Moving {} to trash directory {}'.format(f, trash_directory))
                    shutil.move(img_directory + '/' + f, trash_directory + '/' + f)
            except Exception as ex:
                log_file.write('{} had exception {}\n'.format(f, ex))


@click.command()
@click.option('--source_dir', required=True, help='Source directory of images')
@click.option('--trash_dir', required=True, help='Destination directory of images to trim/remove')
def main(source_dir: str, trash_dir: str):
    coloredlogs.install(level='INFO')
    process(source_dir, trash_dir)


if __name__ == '__main__':
    main()
