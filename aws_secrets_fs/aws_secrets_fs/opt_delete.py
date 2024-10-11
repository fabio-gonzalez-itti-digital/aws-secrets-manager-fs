from . import utils
from . import aws


def run(secret_name: str, profile: str, region: str):
    """
    Elimina un secreto existente en AWS Secrets Manager.
    Parameters:
        secret_name: Nombre o ARN de secreto a eliminar.
        profile: Perfil aws a utilizar.
        region: Región aws a utilizar, si hubiere.
    """
    try:
        # Eliminar secreto.
        print(f"Eliminando: \"{secret_name}\".")
        _, err = aws.delete_secret(secret_name, profile, region)
        if err != None:
            raise err
        print("Secret eliminado.")
    except Exception as e:
        print("Error: " + str(e))
        print(utils.bcolors.FAIL + "Error: no se puedo eliminar el secreto indicado." + utils.bcolors.ENDC)
