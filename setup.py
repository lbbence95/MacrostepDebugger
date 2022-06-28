#!/usr/bin/env -e python

# Macrostep debugger v0.6 (2022.06.)

import setuptools

setuptools.setup(
    name='Cloud-based Macrostep Debugger',
    version='0.6',
    author='ELKH SZTAKI-LPDS',
    packages=[
        'api',
		'bpgen',
        'controller',
        'controller.orchestratorhandler',
        'controller.orchestratorhandler.plugins',
        'data',
        'util'
    ],
    scripts=[
        'bin/debugger',
        'bin/debugger-app',
		'bin/debugger-generate',
        'bin/debugger-list',
        'bin/debugger-step',
        'bin/debugger-play'
    ]
)