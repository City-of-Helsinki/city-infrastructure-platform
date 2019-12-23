from setuptools import find_packages, setup

setup(
    name='city-infrastructure-platform',
    version='0.0.1',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[l for l in open("requirements.txt", "rt").readlines() if l and not l.startswith("#")],
    zip_safe=False,
)
