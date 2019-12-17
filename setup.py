import os
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    # python must be greater than 3.5 because of https://www.python.org/dev/peps/pep-0484/
    # python must be greater than 3.6 because of https://www.python.org/dev/peps/pep-0526/
    raise RuntimeError("Intrst_algrms 3.x requires Python 3.6+")


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

install_requires = [
    'requests>=2.22.0',
    'selenium>=3.141.0',
    'python-dotenv==0.10.3'
]

tests_require = [

]

extras_require = {
    'docs': [
        'Sphinx',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup(
    name="py_parser_sber",
    author="Nikolai Vidov",
    author_email="lastsal@mail.ru",
    version='0.0.1',
    description="Simple parser of Sberbank, using selenium",
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    license="MIT",
    keywords="parser sber Sberbank ",
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    entry_points = {
        'console_scripts': [
            'py_parser_sber_run_once = py_parser_sber.main:py_parser_sber_run_once',
            'py_parser_sber_run_infinite = py_parser_sber.main:py_parser_sber_run_infinite',
        ],
    },
    python_requires='>=3.6',
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=tests_require,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)