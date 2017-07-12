# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='fedmsg_genacls',
    version='0.6',
    description='A fedmsg consumer that sets gitosis acls in response to pkgdb messages',
    license="LGPLv2+",
    author='Janez Nemanič and Ralph Bean',
    author_email='admin@fedoraproject.org',
    url='https://github.com/fedora-infra/fedmsg-genacls',
    install_requires=[
        "fedmsg",
        "python-fedora",
        "arrow",
    ],
    packages=[],
    py_modules=['fedmsg_genacls'],
    entry_points="""
    [moksha.consumer]
    fedmsg_genacls = fedmsg_genacls:GenACLsConsumer
    fedmsg_gitoliteprefix = fedmsg_genacls:GitolitePrefixConsumer
    """,
)
