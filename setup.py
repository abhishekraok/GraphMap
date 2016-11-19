# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('LICENSE') as f:
    license = f.read()

setup(
    name='graphmap',
    version='0.0.2',
    description='Images on a quad graph',
    author='Abhishek Rao',
    author_email='abhishek.rao.comm@gmail.com',
    url='https://github.com/abhishekraok/GraphMap',
    download_url='https://github.com/abhishekraok/GraphMap/archive/v0.1.tar.gz',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

