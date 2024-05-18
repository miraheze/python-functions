"""Controls the setup of the package by setuptools/pip."""
from setuptools import find_packages, setup

from miraheze.version import VERSION

with open('README.md') as readme_file:
    readme = readme_file.read()


setup(
    name='Miraheze_PyUtils',
    version=VERSION,
    description='Python Utilities for Miraheze',
    long_description=readme,
    long_description_content_type='text/markdown',  # This is important!
    author='RhinosF1',
    author_email='rhinosf1@wikitide.org',
    maintainer='Miraheze Technology Team',
    maintainer_email='sre@wikitide.org',
    url='https://github.com/miraheze/python-functions',
    packages=find_packages('.'),
    include_package_data=True,
    test_suite='tests',
    license='GPL3',
)
