from setuptools import setup

setup(
    name = "pytonisacommons",
    version = "1.0.0",
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
    # long_description=read('README'),
)