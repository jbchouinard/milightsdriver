from setuptools import setup, find_packages


setup(
    name = 'milightsdriver',
    version = '1.0.0',
    author = 'jbch',
    packages = find_packages(),
    install_requires = ['requests'],
    entry_points = {
        'console_scripts': ['scheduler=milightsdriver.scheduler:main']
    }
)