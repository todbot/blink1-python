from setuptools import setup
#import os

#PROJECT_ROOT, _ = os.path.split(__file__)
REVISION = '0.1.2'
PROJECT_NAME = 'blink1'
PROJECT_AUTHORS = "Salim Fadhley, Tod E. Kurt"
PROJECT_EMAILS = 'salimfadhley@gmail.com, todbotdotcom@gmail.com'
PROJECT_URL = "https://github.com/todbot/blink1-python"
SHORT_DESCRIPTION = 'Official blink(1) control library'

#try:
#    DESCRIPTION = open(os.path.join(PROJECT_ROOT, "README.md")).read()
#except IOError:
#    DESCRIPTION = SHORT_DESCRIPTION


setup(
    name=PROJECT_NAME.lower(),
    version=REVISION,
    author=PROJECT_AUTHORS,
    author_email=PROJECT_EMAILS,
    packages=['blink1', 'blink1_tests'],
    zip_safe=True,
    include_package_data=False,
    install_requires=['hidapi>=0.7.99', 'click', 'webcolors'],
    test_suite='nose.collector',
    tests_require=['mock', 'nose', 'coverage'],
    url=PROJECT_URL,
    description=SHORT_DESCRIPTION,
    long_description_markdown_filename='README.md',  # uses setuptools-markdown
    license='MIT',
    entry_points={
        'console_scripts': [
            'blink1-flash = blink1.flash:flash',
            'blink1-shine = blink1.shine:shine'
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing',
    ],
)
