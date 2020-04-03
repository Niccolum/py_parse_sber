"""Setup file for project."""

from pathlib import Path
import sys

from setuptools import (
    find_packages,
    setup,
)


TEST_VERSION = '0.0.dev1'

if sys.version_info < (3, 6):
    # python must be greater than 3.5 because of https://www.python.org/dev/peps/pep-0484/
    # python must be greater than 3.6 because of https://www.python.org/dev/peps/pep-0526/
    raise RuntimeError("py_parse_sber 3.x requires Python 3.6+")


def read(fname: str) -> str:
    """Read file starts from root directory."""
    with (Path(__file__).resolve().parent / fname).open() as f:
        return f.read()


def get_version():
    try:
        return read('VERSION')
    except FileNotFoundError:
        return TEST_VERSION


install_requires = [
    'requests==2.22.0',
    'selenium==3.141.0'
]

static_analysis_require = [
    'cohesion',  # A tool for measuring Python class cohesion
    'flake8',  # Main runner, python code checker
    'flake8-broken-line',  # Flake8 plugin to forbid backslashes (\) for line breaks
    'flake8-bugbear',  # A plugin for Flake8 finding likely bugs and design problems in your program.
    'flake8-builtins',  # Check for python builtins being used as variables or parameters.
    'flake8-cognitive-complexity',  # An extension for flake8 that validates cognitive functions complexity.
    'flake8-comprehensions',  # A flake8 plugin that helps you write better list/set/dict comprehensions.
    'flake8-docstrings',  # A simple module that adds an extension for the fantastic pydocstyle tool to flake8.
    'flake8-fixme',  # Check for temporary developer notes.
    'flake8-import-order',  # Flake8 plugin that checks import order against various Python Style Guides
    'flake8-mutable',  # Find mutable variables as default funcs value
    'flake8-mypy',  # A plugin for Flake8 integrating mypy.
    'flake8-print',  # Check for Print statements in python files.
    'pep8-naming',  # Check your code against PEP 8 naming conventions.
    'radon'  # Radon is a Python tool that computes various metrics from the source code.
]

vulnerability_check_require = [
    'bandit',
]

docs_require = [
    'Sphinx',
]

tests_require = [
    'pytest',
]

extras_require = {
    'static_analysis': static_analysis_require,
    'vulnerability_check': vulnerability_check_require,
    'docs': docs_require,
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup(
    name="py_parser_sber",
    author="Nikolai Vidov",
    author_email="lastsal@mail.ru",
    version=get_version(),
    description="Simple parser of Sberbank, using selenium",
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/Niccolum/py_parse_sber',
    license="MIT",
    keywords="parser sber Sberbank ",
    platforms='any',
    packages=find_packages(exclude=('tests', 'docker')),
    package_data={'': ['VERSION', '*.json', '*.yml', '*.md', '*.txt']},
    entry_points={
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
        'Development Status :: 4 - Beta',
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
