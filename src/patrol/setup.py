from setuptools import setup

setup(
    name='patrol',
    version='0.1.0',
    packages=['patrol'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/patrol']),
        ('share/patrol', ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ROS course example',
    maintainer_email='noreply@example.invalid',
    description='PR03: Pose subscription, timer and cmd_vel remapping',
    license='Apache-2.0',
    entry_points={'console_scripts': ['patrol = patrol.patrol:main']},
)
