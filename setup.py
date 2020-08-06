# Setup file

import  setuptools

setuptools.setup(
    name='macro-debugger',
    version='0.1',
    author='Bence Ligetfalvi & SZTAKI',
    packages=[
        'src',
        'src.api',
        'src.controller',
        'src.data',
        'src.util'
        ],
    scripts=[
        'bin/macro-debugger-rest'
    ]
)