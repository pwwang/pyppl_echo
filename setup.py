# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme = ''

setup(
    long_description=readme,
    name='pyppl_echo',
    version='0.0.5',
    description='Echo script output to PyPPL logs',
    python_requires='==3.*,>=3.6.0',
    author='pwwang',
    author_email='pwwang@pwwang.com',
    license='MIT',
    entry_points={"pyppl": ["pyppl_echo = pyppl_echo"]},
    packages=[],
    package_dir={"": "."},
    package_data={},
    install_requires=['pyppl'],
    extras_require={"dev": ["pytest", "pytest-cov"]},
)
