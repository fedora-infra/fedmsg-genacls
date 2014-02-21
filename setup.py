from setuptools import setup

setup(
    name='fedmsg_genacls',
    version='0.0.1',
    description='',
    author='',
    author_email='',
    url='',
    install_requires=["fedmsg"],
    packages=[],
    entry_points="""
    [moksha.consumer]
    fedmsg_genacls = fedmsg_genacls:GenACLsConsumer
    """,
)
