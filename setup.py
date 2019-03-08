import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-pessimist_locking',
    version=__import__('pessimist_locking').VERSION,
    packages=find_packages(),
    include_package_data=True,
    description='soft pessimistic locking extension for django',
    long_description=README,
    url='https://www.zayazza.de/',
    author='zayazza gmbh',
    author_email='dev@zayazza.de',
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
