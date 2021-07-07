import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="winix",
    version="0.3.0",
    author="Hunter Fernandes",
    author_email="hunter@hfernandes.com",
    description="Programmatically control the Winix C545",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hfern/winix",
    packages=setuptools.find_packages(),
    install_requires=["warrant", "warrant_lite", "requests",],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": ["winix = winix.cmd:main", "winixctl = winix.cmd:main",],
    },
)
