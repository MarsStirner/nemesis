import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from nemesis.nemesis_version import version


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='nemesis',
    version=version,
    url='https://github.com/hitsl/nemesis',
    author='hitsl',
    description='Base MIS module.',
    long_description=read('README.md'),
    include_package_data=True,
    packages=['nemesis'],
    platforms='any',
    #test_suite='nemesis.tests',
    install_requires=[
        'Flask',
        'SQLAlchemy==0.9.9',
        'Flask-SQLAlchemy',
        'pytz',
        'Flask-BabelEx',
        'Flask-Cache',
        'Requests',
        'sphinxit',
        'Flask-Beaker',
        'Flask-Login==0.2.11',
        'Flask-Principal',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
