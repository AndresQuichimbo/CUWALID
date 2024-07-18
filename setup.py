from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="CUWALID",
    version="0.9.2", 
    author="Andrés Quichimbo, Manuel Rios Gaona, Dagmawi Teklu Asfaw",
    author_email="cootelf@cardiff.ac.uk",
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
    python_requires='>=3.9',
    install_requires = [
        'requests',
        'geopandas',
        'rioxarray',
        'dask',
        'landlab',
        'pointpats',
        'scikit-image',
        'pip-tools',
        'chardet',
        'tqdm',
        'numpy',
        'Cartopy',
        'metpy',
        'numba',
        'cmaps',      
        'cmcrameri',    
        'seaborn', 
        'spyder-kernels',  
        'ipykernel',       
        'basemap',         
        'bottleneck'
        ],
    include_package_data=True,
)