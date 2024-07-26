import boto3


def retrieve_secret(secret_name: str, profile: str) -> tuple[str, None] | tuple[None, Exception]:
    """
    Obtiene el valor de un secreto desde aws secrets manager.
    secret_name: Nombre del secreto a recuperar.
    profile: Perfil aws a utilizar.
    """
    session = boto3.Session(profile_name=profile)
    client = session.client('secretsmanager')
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name)
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
    secret_name: Nombre del secreto a actualizar.
    secret_value: Nuevo valor para secreto.
    profile: Perfil aws a utilizar.
    """
    session = boto3.Session(profile_name=profile)
    client = session.client('secretsmanager')
    try:
        response = client.update_secret(
            SecretId=secret_name, SecretString=secret_value)
        return response, None
    except Exception as e:
        return None, e


def create_secret(secret_name: str, secret_value: str, profile: str) -> tuple[any, None] | tuple[None, Exception]:
    """
    Registra el valor para un nuevo secreto en aws secrets manager.
    secret_name: Nombre del secreto a crear.
    secret_value: Valor para secreto.
    profile: Perfil aws a utilizar.
    """
    session = boto3.Session(profile_name=profile)
    client = session.client('secretsmanager')

    try:
        response = client.create_secret(
            Name=secret_name,
            SecretString=secret_value
        )
        return response, None
    except Exception as e:
        return None, e
