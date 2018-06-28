import os
from setuptools import setup, find_packages

src_dir = os.path.dirname(__file__)

install_requires = [
    "python-dateutil<3.0.0",
    "stacker>=1.0.1",
    "troposphere>=2.2.2",
    "awacs>=0.6.0",
]

tests_require = [
    "coverage>=4.5.1",
    "mock~=2.0.0",
    "stacker>=1.1.1",
]

setup_requires = [
    "nose>=1.0",
]


def read(filename):
    full_path = os.path.join(src_dir, filename)
    with open(full_path) as fd:
        return fd.read()


if __name__ == "__main__":
    setup(
        name="stacker_blueprints",
        version="1.0.7",
        author="Michael Barrett",
        author_email="loki77@gmail.com",
        license="New BSD license",
        url="https://github.com/remind101/stacker_blueprints",
        description="Default blueprints for stacker",
        long_description=read("README.rst"),
        packages=find_packages(),
        setup_requires=setup_requires,
        install_requires=install_requires,
        tests_require=tests_require,
        test_suite="nose.collector",
    )
