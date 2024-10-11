from . import utils
from . import aws


def run() -> None:
    """
    Verifica las dependencias necesarias. De momento, que esté instalado aws cli.

    Se imprime la versión encontrada y los perfiles configurados.
    """
    # Verificar si aws cli esta disponible.
    aws_cli_available = aws.aws_cli_available()
    if aws_cli_available == False:
        print(utils.bcolors.FAIL + "Error: No se encontró AWS CLI." + utils.bcolors.ENDC)
        exit(1)

    # Versión de aws cli.
    aws_version = aws.aws_cli_version()
    if aws_version == None:
        print(utils.bcolors.FAIL + "Error: No se pudo determinar la versión de AWS CLI." + utils.bcolors.ENDC)
        exit(1)
    print("AWS CLI Version: {0}{1}{2}".format(utils.bcolors.OKGREEN, aws_version, utils.bcolors.ENDC))

    # Listar perfiles disponibles.
    try:
        # Obtener perfiles.
        aws_profiles = aws.aws_cli_profiles()
        if aws_profiles == None:
            raise RuntimeWarning("No se pudieron obtener perfiles.")

        # Listar perfiles.
        print("AWS CLI Profiles:")
        for aws_profile in aws_profiles:
            print("  • {0}".format(aws_profile))
    except Exception:
        print(utils.bcolors.WARNING + "Advertencia: \"aws configure list-profiles\" no soportado." + utils.bcolors.ENDC)
        exit(1)
