# -*- coding: utf-8 -*-

import os
import re
import hashlib
import tempfile
import shutil
from PySide6.QtWidgets import QFileDialog
from xml.etree import ElementTree
from xml.dom import minidom

from singletons.config import config
from singletons.interface import interface


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


@static_vars(directory=None)
def opendir(f=None):
    if opendir.directory is None:
        opendir.directory = f if f else os.path.abspath('.')
    dialog = QFileDialog(directory=opendir.directory)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    if dialog.exec():
        directory = dialog.selectedFiles()[0]
        openfile.directory = directory
        return directory
    return None


@static_vars(directory=None)
def openfile(f, many=False):
    if openfile.directory is None:
        openfile.directory = config.value('temporary', 'directory')
    dialog = QFileDialog(filter=f, directory=openfile.directory)
    dialog.setFileMode(QFileDialog.ExistingFiles if many else QFileDialog.ExistingFile)
    if dialog.exec():
        files = dialog.selectedFiles()
        openfile.directory = os.path.dirname(files[0])
        config.set_value('temporary', 'directory', openfile.directory)
        return files if many else files[0]
    return None


def savefile(f, suffix, filename='') -> str:
    dialog = QFileDialog(directory=filename)
    dialog.setDefaultSuffix(suffix)
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    dialog.setNameFilters([f])
    return dialog.selectedFiles()[0] if dialog.exec() == QFileDialog.Accepted else None


def open_supported(many=False):
    formats = [
        interface.text('System', 'All files') + ' (*.package *.stbl *.xml)',
        interface.text('System', 'Packages') + ' (*.package)',
        interface.text('System', 'STBL files') + ' (*.stbl)',
        interface.text('System', 'XML files') + ' (*.xml)',
    ]
    return openfile(';;'.join(formats), many=many)


def open_xml():
    formats = [
        interface.text('System', 'XML files') + ' (*.xml)',
    ]
    return openfile(';;'.join(formats))


def save_xml(filename: str = '') -> str:
    return savefile(interface.text('System', 'XML files') + ' (*.xml)', 'xml', filename)


def save_stbl(filename: str = '') -> str:
    return savefile(interface.text('System', 'STBL files') + ' (*.stbl)', 'STBL', filename)


def save_package(filename: str = '') -> str:
    return savefile(interface.text('System', 'Packages') + ' (*.package)', 'package', filename)


def create_temporary_copy(path: str) -> str:
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, os.path.basename(path))
    shutil.copy2(path, temp_path)
    return temp_path


def text_to_table(text):
    if text:
        text = text.replace("\r", '')
        text = re.sub(r'(\\n)+', '  ', text)
        text = re.sub(r'\n+', '  ', text)
        return text
    return ''


def text_to_edit(text):
    return re.sub(r'\\n', "\n", text) if text else ''


def text_to_stbl(text):
    return text.replace("\r", '').replace("\n", '\\n') if text else ''


def compare(text1, text2):
    return text_to_stbl(text1) == text_to_stbl(text2)


def md5(string):
    hash_object = hashlib.md5(string.encode('utf-8'))
    return hash_object.hexdigest()


def _hash(value, init, prime, mask):
    if isinstance(value, str):
        value = value.lower().encode()
    h = init
    for byte in value:
        h = (h * prime) & mask
        h = h ^ byte
    return h


def fnv32(value):
    return _hash(value, 0x811c9dc5, 0x1000193, (1 << 32) - 1)


def fnv64(value):
    return _hash(value, 0xCBF29CE484222325, 0x100000001b3, (1 << 64) - 1)


def prettify(node):
    rough = ElementTree.tostring(node, encoding='utf-8').decode('utf-8')
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(indent='  ', encoding='utf-8')


def parsexml(content):
    return ''.join((re.sub(r'<(\w+)', r'<\1 DUMMY_LINE="' + str(i + 1) + '"', line) for i, line in enumerate(content)))
