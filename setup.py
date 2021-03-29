from setuptools import find_packages
from distutils.core import setup

setup(
    name='aiomysql',
    version='1.0.0',
    packages=find_packages(exclude=['tests']),
    description='asyncio mysql tools',
    long_description="""
Documentation
-------------
    You can see the project and documentation at the `GitHub repo <https://github.com/robertchase/aiomysql>`_
    """,
    author='Bob Chase',
    url='https://github.com/robertchase/aiomysql',
    license='MIT',
)
