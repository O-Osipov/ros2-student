from glob import glob

from setuptools import find_packages, setup

name = 'course_simulation'

setup(
    name=name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + name]),
        ('share/' + name, ['package.xml']),
        ('share/' + name + '/launch', glob('launch/*.launch.py')),
        ('share/' + name + '/config', glob('config/*.yaml')),
        ('share/' + name + '/worlds', glob('worlds/*.sdf')),
        ('share/' + name + '/models/course_ackermann',
         glob('models/course_ackermann/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='O-Osipov',
    maintainer_email='213808971+O-Osipov@users.noreply.github.com',
    description='PR07 Gazebo simulation and adapters',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={'console_scripts': [
        'drive_adapter = course_simulation.drive_adapter:main',
        'odom_adapter = course_simulation.odom_adapter:main',
        'command_probe = course_simulation.command_probe:main',
    ]},
)
