"""Controls the setup of the package by setuptools/pip."""
from setuptools import find_packages, setup

from miraheze.version import VERSION

with open('README.md') as readme_file:
    readme = readme_file.read()


with open('requirements.txt') as requirements_file:
    requirements = list(requirements_file.readlines())


setup(
    name='Miraheze_PyUtils',
    version=VERSION,
    description='Python Utilities for Miraheze',
    long_description=readme,
    long_description_content_type='text/markdown',  # This is important!
    author='RhinosF1',
    author_email='rhinosf1@wikitide.org',
    url='https://github.com/miraheze/python-functions',
    packages=find_packages('.'),
    include_package_data=True,
    install_requires=requirements,
    test_suite='tests',
    license='GPL3',
)
