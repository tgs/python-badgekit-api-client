import codecs

from os import path
from setuptools import find_packages, setup


def read(*parts):
    filename = path.join(path.dirname(__file__), *parts)
    with codecs.open(filename, encoding="utf-8") as fp:
        return fp.read()


setup(
    author="Thomas Grenfell Smith",
    author_email="thomathom@gmail.com",
    description="Python client for Mozilla's BadgeKit API",
    name="badgekit-api-client",
    long_description=read("README.md"),
    version=read("badgekit/version.py").split('=')[1].strip().strip('"'),
    # url="http://badgekit-api-client.rtfd.org/",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        'requests',
        'requests-jwt>=0.3',
        'setuptools',
        ],
    tests_require=[
        'httpretty',
        ],
    test_suite='test.suite',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    zip_safe=False
)
