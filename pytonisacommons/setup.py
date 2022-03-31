from setuptools import setup

setup(
    name = "pytonisacommons",
    version = "2.0.1",
    author = "Luís Chaves",
    author_email = "luis.chaves_@outlook.com",
    description = ("This package contains common code for other modules of the pythonisa-ocr-bot"),
    license = "Mozilla Public License Version 2.0",
    keywords = "pytonisa commons",
    url = "https://github.com/LuisF3/pytonisa-ocr-bot",
    packages=[
        'pytonisacommons',
        'pytonisacommons.configs',
        'pytonisacommons.objects',
        ],
    install_requires=[
        'nanoid==2.0.0',
        'boto3==1.21.27'
    ],
    # long_description=read('README'),
)
