#!/usr/bin/env -e python

# Macrostep debugger v0.2 (2021.02.)

import setuptools

setuptools.setup(
    name='MSTEP-API',
    version='0.2',
    author='SZTAKI-LPDS',
    packages=[
        'controller',
        'data',
        'util'
    ],
    scripts=[
        'bin/debugger-app.py',
        'bin/debugger-list.py',
        'bin/debugger-trace.py',
        'bin/debugger-step.py',
        'bin/debugger-replay.py'
    ]
)