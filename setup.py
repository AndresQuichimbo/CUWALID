from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="cuwalid",
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    version="1.1.40", 
=======
    version="1.1.42", 
>>>>>>> Stashed changes
=======
    version="1.1.42", 
>>>>>>> Stashed changes
    author="Andrés Quichimbo, Manuel Rios Gaona, Dagmawi Teklu Asfaw, Leo Coote",
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
        'numpy<2.0',
        'Cartopy',
        'metpy',
        'numba',
        'cmaps',      
        'cmcrameri',    
        'seaborn', 
        'spyder-kernels',  
        'ipykernel',       
        'basemap',         
        'bottleneck',
        'matplotlib-scalebar',
        'osmnx',
        'geopy',
        'fitter',
        'rasterstats',
        'lmfit',
        'python-bidi',
        'arabic-reshaper',
        'osmium'
        ],
    include_package_data=True,
)