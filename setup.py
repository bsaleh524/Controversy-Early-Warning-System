from setuptools import setup, find_packages

setup(
    name='ControversyEarlyWarningSystem',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'google-api-python-client',
        'sentence-transformers',
        'scikit-learn',
    ],
    author='bsaleh524',
    description='A system to build a graph of YouTube channels based on content similarity.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/bsaleh524/Controversy-Early-Warning-System',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)