from setuptools import setup

setup(
    name='genacls_consumer',
    version='0.0.1',
    description='',
    author='',
    author_email='',
    url='',
    install_requires=["fedmsg"],
    packages=[],
    entry_points="""
    [moksha.consumer]
    genacls_consumer = genacls_consumer:GenACLsConsumer
    """,
)
