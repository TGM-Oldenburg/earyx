from setuptools import setup, find_packages
setup(
    name = "earyx",
    version = "0.1",
    packages=find_packages(exclude=['docs']),
    package_data={'earyx.gui': ['*.html', '*.js']},
    include_package_data=True,

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['pysoundfile>=0.8', 'sounddevice', 'matplotlib',
                        'tornado', 'cffi', 'numpy'],


    # metadata for upload to PyPI
    author = "Matthias Stennes",
    author_email = "earyx@m.stennes.org",
    description = "Next generation psylab",
    license = "GNU GPL",
    keywords = "audio psycoacustics",
    url = "https://github.com/stvol/earyx",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
