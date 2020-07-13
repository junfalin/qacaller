import setuptools

try:
    import pypandoc

    long_description = pypandoc.convert_file('README.md', 'rst')
except Exception:
    long_description = ""
install_requires = ['mlflow==1.8.0',
                    'click==7.1.2']
setuptools.setup(
    name="qacaller",
    version="0.0.5",
    author="faithforus",
    author_email="ljunf817@163.com",
    description="power by mlflow tracking",
    long_description=long_description,
    install_requires=install_requires,
    keywords="python package log tracking",
    url="https://github.com/Faithforus/qacaller",
    license="MIT",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['qacaller = qacaller.listener:cmdline']
    },
)
