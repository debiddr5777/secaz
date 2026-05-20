from setuptools import setup

setup(
    name='secaz',
    version='1.0.0',
    description='Linux GUI Application Uninstaller — discover and remove apps via .desktop files',
    py_modules=['secaztool', 'core'],
    install_requires=[
        'click',
    ],
    entry_points={
        'console_scripts': [
            'secaz=secaztool:cli',
        ],
    },
)
