from setuptools import setup, find_packages
import sys, os

version = "0.1"

setup(name="zdfversion",
      version=version,
      description="Make PDFs out of Zendesk forums.",
      long_description="Make PDFs out of Zendesk forums.",
      classifiers=["Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Documentation",
      ],
      keywords="zendesk pdf",
      author="Brian Shumate",
      author_email="bshumate@basho.com",
      url="http://www.basho.com",
      license="Apache",
      packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
      include_package_data=True,
      zip_safe=False,
      requires=["pycurl",
        "xhtml2pdf",
      ]
)
