from setuptools import setup, find_packages
import sys, os

version = "0.1"

setup(name="zdf2pdf",
      version=version,
      scripts=["bin/zdf2pdf"],
      description="Make PDFs out of Zendesk forums.",
      long_description="Make PDFs out of Zendesk forums.",
      classifiers=["Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Documentation",
      ],
      keywords="zendesk pdf",
      author="Brent Woodruff",
      author_email="brent@fprimex.com",
      url="http://github.com/basho/zdf2pdf",
      license="Apache",
      packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
      include_package_data=True,
      zip_safe=False,
      install_requires=["xhtml2pdf",
        "beautifulsoup4",
        "httplib2",
        "simplejson",
        "zendesk",
        "configparser",
      ]
)
