"""A setuptools based setup module."""

import setuptools

import obelisk

setuptools.setup(
    name='obelisk-python',
    version=obelisk.__version__,
    url='https://gitlab.ilabt.imec.be/predict/obelisk-python',
    author='Pieter Moens',
    author_email='pieter.moens@ugent.be',
    description='Python client for Obelisk',
    long_description=open('README.md').read(),
    packages=['obelisk'],
    platforms='any',
    install_requires=[line.split('#')[0] for line in open('requirements.txt').readlines()],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.6',
    # Some extras, for when necessary:
    # (see https://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/)
    # test_suite='contextawareml.test.test_contextawareml',
    # tests_require=['pytest'],
    # license='Apache Software License',
    # cmdclass={'test': PyTest}
    # zip_safe=False,
    # include_package_data=True,
)
