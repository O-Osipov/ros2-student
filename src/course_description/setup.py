from glob import glob

from setuptools import find_packages, setup

name = 'course_description'

setup(
    name=name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + name]),
        ('share/' + name, ['package.xml']),
        ('share/' + name + '/urdf', glob('urdf/*.urdf.xacro')),
        ('share/' + name + '/launch', glob('launch/*.launch.py')),
        ('share/' + name + '/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='O-Osipov',
    maintainer_email='213808971+O-Osipov@users.noreply.github.com',
    description='PR06 Ackermann robot description and tf launch',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
)
