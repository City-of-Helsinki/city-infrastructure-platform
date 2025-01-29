from setuptools import find_packages, setup

setup(
    name="city-infrastructure-platform",
    version="1.5.0",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[line for line in open("requirements.txt", "rt").readlines() if line and not line.startswith("#")],
    zip_safe=False,
)
