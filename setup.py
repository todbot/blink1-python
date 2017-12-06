from setuptools import setup

setup(name='blink1',
    version='0.1',
    description='blink1 blah blah',
    url='http://github.com/storborg/funniest',
    author='Tod E. Kurt',
    author_email='todbotdotcom@gmail.com',
    license='MIT',
    packages=['blink1'],
    install_requires=['hidapi>=0.7.99', 'click', 'webcolors'],
    zip_safe=False)
