from setuptools import setup
from glob import glob
import os
from pathlib import Path

package_name = 'atlas_sim'

data_files = [
    ('share/ament_index/resource_index/packages', ['resource/atlas_sim']),
    ('share/atlas_sim', ['package.xml']),
    (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
    (os.path.join("share", package_name, "meshes"), glob("meshes/*")),
]

for path in Path("worlds").rglob("*"):
    if path.is_file():
        install_dir = os.path.join(
            "share",
            package_name,
            path.parent.as_posix()
        )
        data_files.append((install_dir, [str(path)]))

setup(
    name=package_name,
    version='0.0.1',
    zip_safe=True,
    maintainer='John Anchery',
    maintainer_email='etcetra7n@gmail.com',
    description='A Mars rover simulation environment for collecting training data',
    license='MIT',
    packages=[package_name],
    data_files=data_files,
    install_requires=['setuptools', 'pynput', 'xacro'],

    entry_points={
        'console_scripts': [
            'sim_window = atlas_sim.sim_window:main'
        ],
    },
)
