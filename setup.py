from setuptools import setup, find_packages

import mailqueue

version = mailqueue.VERSION

setup(name='django-mail-queue',
      version=version,
      description="Simple Mail Queuing for Django",
      long_description=open("README.md", "r").read(),
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Web Environment",
          "Intended Audience :: Developers",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
          "Topic :: Utilities",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 3",
          "Framework :: Django",
          "Framework :: Django :: 1.5",
          "Framework :: Django :: 1.6",
          "Framework :: Django :: 1.7",
          "Framework :: Django :: 1.8",
          "License :: OSI Approved :: MIT License",
          ],
      keywords='django-mail-queue',
      author='Derek Stegelman',
      url='http://github.com/dstegelman/django-mail-queue',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
    )
