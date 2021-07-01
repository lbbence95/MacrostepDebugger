#!/usr/bin/env -e python

# Macrostep debugger v0.4 (2021.06.)

import setuptools

setuptools.setup(
    name='Cloud-based Macrostep Debugger',
    version='0.4',
    author='ELKH SZTAKI-LPDS',
    packages=[
        'api',
        'controller',
        'data',
        'util'
    ],
    scripts=[
        'bin/debugger.py',
        'bin/debugger-app.py',
        'bin/debugger-list.py',
        'bin/debugger-step.py',
        'bin/debugger-play.py'
    ]
)