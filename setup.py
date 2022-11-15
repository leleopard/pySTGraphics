from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pySTGraphics',
      version='1.0',
      description='Python package that provides a collection of 2D graphics openGL objects such as image',
      url='https://github.com/leleopard/pySTGraphics',
      author='Stephane Teisserenc',
      author_email='',
      license='MIT',
      packages=['pySTGraphics'],
      include_package_data=True,
      zip_safe=False)
