from setuptools import setup, find_packages

setup(
    name='foxy-farmer',
    version='1.0.0',
    packages=find_packages(),
    url='https://foxypool.io',
    license='GPLv3',
    author='Felix Brucker',
    author_email='contact@foxypool.io',
    description='A simplified farmer for the Chia blockchain using the foxy chia farming gateway.',
    install_requires=[
        "chia-blockchain@git+https://github.com/foxypool/chia-blockchain#egg=chia-blockchain",
    ],
    extras_require=dict(
        dev=[
            "pyinstaller==5.8.0",
        ]
    ),
    entry_points={
        "console_scripts": [
            "foxy-farmer = foxy_farmer.foxy_farmer:main",
        ],
    },
)
