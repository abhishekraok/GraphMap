# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='graphmap',
    version='0.0.6',
    description='Images on a quad graph. Create an infinite canvas',
    author='Abhishek Rao',
    author_email='abhishek.rao.comm@gmail.com',
    url='https://github.com/abhishekraok/GraphMap',
    download_url='https://github.com/abhishekraok/GraphMap/archive/v0.0.4.tar.gz',
    packages=find_packages(exclude=('tests', 'docs'))
)

