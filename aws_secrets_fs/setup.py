
from setuptools import setup

setup(
    name='aws_secrets_fs',
    version='0.0.1',
    description='Herramienta que permite sincronizar archivos con datos sensibles, utilizando AWS Secrets Manager como backend.',
    url='https://github.com/fabio-gonzalez-itti/aws-secrets-manager-fs',
    author='Fabio Antonio González Sosa',
    author_email='fabio.gonzalez@itti.digital',
    license='MIT',
    packages=['src'],
    install_requires=[
        'boto3==1.34.120'
    ]
)
