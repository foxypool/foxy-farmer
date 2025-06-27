from sys import platform

from setuptools import find_packages, setup

dependencies = [
    "aiohttp>=3.10.4",
    "aioudp==1.0.1",
    "chia-blockchain@git+https://github.com/foxypool/chia-blockchain@2.5.4-og-1.6.1#egg=chia-blockchain",
    "click>=8.1.7",
    "colorlog>=6.9.0",
    "humanize==4.11.0",
    "packaging>=24.0",
    "pyparsing==3.2.0",
    "PyYAML>=6.0.2",
    "questionary==2.0.1",
    "sentry-sdk==2.17.0",
    "StrEnum==0.4.15",
    "yaspin==3.1.0",
]
if platform == "win32" or platform == "cygwin":
    dependencies.append("pywin32>=306")

setup(
    name='foxy-farmer',
    version='1.24.0',
    url='https://foxypool.io',
    license='GPLv3',
    author='Felix Brucker',
    author_email='contact@foxypool.io',
    description='A simplified farmer for the Chia blockchain using the foxy chia farming gateway.',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires='>=3.9, <4',
    install_requires=dependencies,
    packages=find_packages(include=["foxy_farmer", "foxy_farmer.*"]),
    extras_require=dict(
        dev=[
            "pyinstaller>=5.12",
        ]
    ),
    entry_points={
        "console_scripts": [
            "foxy-farmer = foxy_farmer.foxy_farmer_main:main",
        ],
    },
)
