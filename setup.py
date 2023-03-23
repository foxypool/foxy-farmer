from setuptools import setup

setup(
    name='foxy-farmer',
    version='1.1.0',
    url='https://foxypool.io',
    license='GPLv3',
    author='Felix Brucker',
    author_email='contact@foxypool.io',
    description='A simplified farmer for the Chia blockchain using the foxy chia farming gateway.',
    install_requires=[
        "chia-blockchain@git+https://github.com/foxypool/chia-blockchain@1.7.1-og-1.2.0#egg=chia-blockchain",
        "click==8.1.3"
    ],
    packages=[
        "foxy_farmer",
    ],
    extras_require=dict(
        dev=[
            "pyinstaller==5.8.0",
        ]
    ),
    entry_points={
        "console_scripts": [
            "foxy-farmer = foxy_farmer.foxy_farmer_main:main",
        ],
    },
)
