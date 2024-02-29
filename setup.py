from setuptools import find_packages, setup

setup(
    name='foxy-farmer',
    version='1.18.0',
    url='https://foxypool.io',
    license='GPLv3',
    author='Felix Brucker',
    author_email='contact@foxypool.io',
    description='A simplified farmer for the Chia blockchain using the foxy chia farming gateway.',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires='>=3.11, <4',
    install_requires=[
        "aiohttp>=3.9.1",
        "aioudp==1.0.1",
        "chia-blockchain@git+https://github.com/foxypool/chia-blockchain@2.1.4-og-1.6.0#egg=chia-blockchain",
        "click>=8.1.3",
        "colorlog>=6.7.0",
        "humanize==4.9.0",
        "pyparsing==3.1.1",
        "PyYAML>=6.0.1",
        "questionary==2.0.1",
        "sentry-sdk==1.33.1",
        "yaspin==3.0.1",
    ],
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
