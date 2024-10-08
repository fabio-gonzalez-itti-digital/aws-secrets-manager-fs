import boto3
import shutil
import subprocess


def aws_cli_available() -> bool:
    """
    Verifica si la herramienta CLI de AWS está disponile localmente.
    """
    try:
        command = shutil.which("aws")
        return command != None and command != ""
    except Exception:
        return False


def aws_cli_version() -> str | None:
    """
    Obtiene la versión de la herramienta CLI de AWS
    """
    proc = subprocess.check_output(['aws', '--version'])
    if proc == None or proc == '':
        return None
    return proc.decode("utf-8").strip().split(" ")[0].split("/")[1]


def aws_cli_profiles() -> list[str] | None:
    profiles = list()
    try:
        # NOTE: aws configure list-profiles existe a partir de la versión 2.x.x.
        proc = subprocess.check_output(['aws', 'configure', 'list-profiles'])
        if proc != None:
            lines = proc.decode("utf-8").split('\n')
            for line in lines:
                if line != None:
                    line = line.strip()
                    if line != "":
                        profiles.append(line)
        return profiles
    except Exception:
        return None


def retrieve_secret(secret_name: str, profile: str) -> tuple[str, None] | tuple[None, Exception]:
    """
    Obtiene el valor de un secreto desde aws secrets manager.
    Parameters:
        secret_name: Nombre del secreto a recuperar.
        profile: Perfil aws a utilizar.
    """
    try:
        session = boto3.Session(profile_name=profile)
        client = session.client('secretsmanager')
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString'], None
        else:
            # No textual o no existe.
            # TODO: DAR SOPORTE A ESTE CASO.
            return None, None
    except Exception as e:
        return None, e


def update_secret(secret_name: str, secret_value: str, profile: str) -> tuple[any, None] | tuple[None, Exception]:
    """
    Actualiza el valor de un secreto en aws secrets manager.
    Parameters:
        secret_name: Nombre del secreto a actualizar.
        secret_value: Nuevo valor para secreto.
        profile: Perfil aws a utilizar.
    """
    try:
        session = boto3.Session(profile_name=profile)
        client = session.client('secretsmanager')
        response = client.update_secret(
            SecretId=secret_name, SecretString=secret_value)
        return response, None
    except Exception as e:
        return None, e


def create_secret(secret_name: str, secret_value: str, profile: str) -> tuple[any, None] | tuple[None, Exception]:
    """
    Registra el valor para un nuevo secreto en aws secrets manager.
    Parameters:
        secret_name: Nombre del secreto a crear.
        secret_value: Valor para secreto.
        profile: Perfil aws a utilizar.
    """
    try:
        session = boto3.Session(profile_name=profile)
        client = session.client('secretsmanager')
        response = client.create_secret(
            Name=secret_name,
            SecretString=secret_value
        )
        return response, None
    except Exception as e:
        return None, e


def delete_secret(secret_name: str, profile: str) -> tuple[any, None] | tuple[None, Exception]:
    """
    Elmina un secreto en aws secrets manager.
    Parameters:
        secret_name: Nombre del secreto a eliminar.
        secret_value: Valor para secreto.
        profile: Perfil aws a utilizar.
    """
    try:
        session = boto3.Session(profile_name=profile)
        client = session.client('secretsmanager')
        response = client.delete_secret(
            SecretId=secret_name,
            ForceDeleteWithoutRecovery=True
        )
        return response, None
    except Exception as e:
        return None, e
