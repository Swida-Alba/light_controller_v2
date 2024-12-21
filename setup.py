from setuptools import setup, find_packages

setup(
    name='light_controller_v2',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'pyserial',
        'openpyxl',
        'tk'
    ],
    entry_points={
        'console_scripts': [
            'protocol_setup=protocol_setup:main',
        ],
    },
    author='Kang-Rui Leng',
    author_email='krleng@pku.edu.cn',
    description='A light controller program using Arduino and Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Swida-Alba/light_controller_v2',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)