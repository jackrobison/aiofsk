import os
from setuptools import setup, find_packages  # type: ignore
from aiofsk import __version__, __name__, __email__, __author__, __license__

console_scripts = [
    'aiofsk = aiofsk.__main__:main',
]

package_name = "aiofsk"
base_dir = os.path.abspath(os.path.dirname(__file__))

setup(
    name=__name__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    description="AFSK for asyncio",
    keywords="modem bell202 afsk",
    license=__license__,
    packages=find_packages(exclude=('tests',)),
    entry_points={'console_scripts': console_scripts},
    install_requires=[
        'sounddevice',
        'numpy'
    ]
)
