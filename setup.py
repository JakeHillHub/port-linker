import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='python_tools',
    version='1.0.0',
    description='Link serial ports and tcp sockets together',
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/JakeHillHub/port-linker',
    author='Jake Hill',
    author_email='jakehillgithub@gmail.net',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Tools'
    ],

    keywords='Tools',
    packages=['state', 'core'],
    install_requires=[
        'pyserial',
        'pydux',
        'funcy'
    ]
)
