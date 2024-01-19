"""Controls the setup of the package by setuptools/pip."""
from setuptools import find_packages, setup

from miraheze.version import VERSION

with open('README.md') as readme_file:
    readme = readme_file.read()

#with open('CHANGELOG.md') as history_file:
    #history = history_file.read()
with open('requirements.txt') as requirements_file:
    requirements = list(requirements_file.readlines())

#with open('dev-requirements.txt') as dev_requirements_file:
    #dev_requirements = list(dev_requirements_file.readlines())


setup(
    name='Miraheze_PyUtils',
    version=VERSION,
    description='Python Utilities for Miraheze',
    long_description=readme, #+ '\n\n' + history,
    long_description_content_type='text/markdown',  # This is important!
    author='RhinosF1',
    author_email='rhinosf1@wikitide.org',
    url='https://github.com/FOSSBots/MirahezeBots',
    packages=find_packages('.'),
    include_package_data=True,
    install_requires=requirements,
    #tests_require=dev_requirements,
    test_suite='tests',
    license='GPL3',
)
