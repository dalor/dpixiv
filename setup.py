import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dpixiv",
    version="3.0.1",
    author="dalor",
    author_email="dalor@i.ua",
    description="Tool to simple use pixiv api of site (Python >= 3.5)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dalor/dpixiv",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "aiohttp"
    ],
)