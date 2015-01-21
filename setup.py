from distutils.core import setup

setup(name="redomat",
  version="0.1",
  install_requires=['docker'],
  data_files=[('/usr/bin', ['redomat.py'])],
  packages=["libredo", "libredo.XML_creator"])
