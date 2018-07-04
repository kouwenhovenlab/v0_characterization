from setuptools import setup

setup(
    name='v0_characterization',
    version='0.0.1',

    install_requires=[
        'qcodes',
        'plottr',
        'broadbean',
        'numpy'
    ],

    author='Mikhail Astafev',
    author_email='astafan8@gmail.com',

    description=("Package with code and scripts for performing V0 "
                 "characterization measurements in Delft."),

    license='',

    packages=['v0_utils'],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.6'
        ],

    keywords='v0 characterization',

    url='https://github.com/kouwenhovenlab/v0_characterization'
)