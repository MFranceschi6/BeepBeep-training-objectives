from setuptools import setup, find_packages
from beepbeep.trainingobjectiveservice import __version__


setup(name='beepbeep-trainingobjective',
      version=__version__,
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      entry_points="""
      [console_scripts]
      beepbeep-trainingobjectiveservice = beepbeep.trainingobjectiveservice.run:main
      """)
