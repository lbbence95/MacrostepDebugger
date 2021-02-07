#!/usr/bin/env -e python

# Macrostep debugger v0.2 (2021.02.)

import setuptools

setuptools.setup(
    name='Marcrostep cloud debugger',
    version='0.2',
    author='ELKH SZTAKI-LPDS',
    packages=[
        'api',
        'controller',
        'data',
        'util'
    ],
    scripts=[
        'bin/debugger-app',
        'bin/debugger-list',
        'bin/debugger-trace',
        'bin/debugger-step',
        'bin/debugger-replay'
    ]
)