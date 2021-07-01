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
		'controller.orchestratorhandler',
		'controller.orchestratorhandler.plugins',
        'data',
        'util'
    ],
    scripts=[
        'bin/debugger',
        'bin/debugger-app',
        'bin/debugger-list',
        'bin/debugger-step',
        'bin/debugger-play'
    ]
)