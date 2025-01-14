#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


"""Скрипт парсит файл формата fb2, вытаскивает из него картинки и сохраняет их в папке с таким же названием,
как файл fb2."""


import os
import base64
import io

from xml.etree import ElementTree as ET
from PIL import Image

import sys
sys.path.append('..')

from common import sizeof_fmt, get_file_name_from_binary


def do(file_name, output_dir='output', debug=True):
    dir_fb2 = os.path.basename(file_name)
    dir_im = os.path.join(output_dir, dir_fb2)
    if not os.path.exists(dir_im):
        os.makedirs(dir_im)
    debug and print(dir_im + ':')

    total_image_size = 0
    number = 1

    tree = ET.parse(file_name)
    root = tree.getroot()

    for child in root:
        tag = child.tag
        if "}" in tag:
            tag = tag[tag.index('}') + 1:]

        if tag != 'binary':
            continue

        try:
            im_id = child.attrib['id']
            content_type = child.attrib['content-type']

            im_file_name = get_file_name_from_binary(im_id, content_type)
            im_file_name = os.path.join(dir_im, im_file_name)

            im_data = base64.b64decode(child.text.encode())

            count_bytes = len(im_data)
            total_image_size += count_bytes

            with open(im_file_name, mode='wb') as f:
                f.write(im_data)

            im = Image.open(io.BytesIO(im_data))
            debug and print('    {}. {} {} format={} size={}'.format(
                number, im_id, sizeof_fmt(count_bytes), im.format, im.size
            ))

            number += 1

        except:
            import traceback
            traceback.print_exc()

    file_size = os.path.getsize(file_name)
    debug and print()
    debug and print('fb2 file size =', sizeof_fmt(file_size))
    debug and print('total image size = {} ({:.2f}%)'.format(
        sizeof_fmt(total_image_size), total_image_size / file_size * 100
    ))


if __name__ == '__main__':
    fb2_file_name = '../input/Непутевый ученик в школе магии 1. Зачисление в школу (Часть 1).fb2'
    do(fb2_file_name)
