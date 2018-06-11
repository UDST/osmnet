# Install setuptools if not installed.
try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup, find_packages


# read README as the long description
with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='osmnet',
    version='0.1.5',
    license='AGPL',
    description=('Tools for the extraction of OpenStreetMap street network '
                 'data for use in Pandana accessibility analyses.'),
    long_description=long_description,
    author='UrbanSim Inc.',
    url='https://github.com/UDST/osmnet',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU Affero General Public License v3'
    ],
    packages=find_packages(exclude=['*.tests']),
    install_requires=[
        'requests >= 2.9.1',
        'pandas >= 0.16.0',
        'numpy>=1.10',
        'geopandas>=0.2.1',
        'Shapely>=1.5'
    ]
)
