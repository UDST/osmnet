from setuptools import setup, find_packages

# read README as the long description
with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='osmnet',
    version='0.1.7',
    license='AGPL',
    description=('Tools for the extraction of OpenStreetMap street network '
                 'data for use in Pandana accessibility analyses.'),
    long_description=long_description,
    author='UrbanSim Inc.',
    url='https://github.com/UDST/osmnet',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU Affero General Public License v3'
    ],
    packages=find_packages(exclude=['*.tests']),
    python_requires='>=3',
    install_requires=[
        'geopandas >= 0.11',
        'numpy >= 1.10',
        'pandas >= 0.23',
        'requests >= 2.9.1',
        'shapely >= 1.8'
    ]
)
