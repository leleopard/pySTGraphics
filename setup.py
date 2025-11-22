from setuptools import setup, find_packages

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
      packages = find_packages(),
      #packages=['pySTGraphics', 'pySTGraphics.fonts_resource.*'],
      include_package_data=True,
      package_data = { 'pySTGraphics' : ['fonts_resource/*.ttf','fonts_resource/*.txt' ]},
      install_requires = ['numpy', 'PyOpenGL', 'PyOpenGL_accelerate', 'Pillow'],
      zip_safe=False)
