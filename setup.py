from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="CUWALID",
    version="0.0.1", 
    author="Andrés Quichimbo, Manuel Rios Gaona, Dagmawi Teklu Asfaw",
    author_email="your.email@example.com",
    description="CUWALID (Climate into Useful Water And Land Information in Drylands)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CornishLeo/CUWALID",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        # List your package dependencies here
        # e.g., 'numpy', 'pandas'
    ],
    include_package_data=True,
)