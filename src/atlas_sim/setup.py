from setuptools import setup
from glob import glob
import os

package_name = 'atlas_sim'

setup(
    name=package_name,
    version='0.0.1',
    zip_safe=True,
    maintainer='John Anchery',
    maintainer_email='etcetra7n@gmail.com',
    description='A Mars rover simulation environment for collecting training data',
    license='MIT',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/atlas_sim']),
        ('share/atlas_sim', ['package.xml']),
        (os.path.join('share', 'atlas_sim', 'launch'), glob('launch/*.py')),
        (os.path.join('share', 'atlas_sim', 'urdf'), glob('urdf/*')),
        (os.path.join('share', 'atlas_sim', 'worlds'), glob('worlds/*')),
    ],
    install_requires=['setuptools', 'pynput', 'xacro'],

    entry_points={
        'console_scripts': [
            'cam_view = atlas_sim.cam_view:main',
            "controls = atlas_sim.controls:main"
        ],
    },
)
