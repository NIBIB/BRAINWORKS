from setuptools import setup

"""
Setuptools config for the command line tool
"""

setup(
    name='brain',
    version='0.0.1',
    py_modules=['cli'],
    install_requires=['Click'],
    entry_points={
        'console_scripts': [
            'brain = utils.cli:cli',
        ],
    },
)