import argparse
import os
import json
import base64
from . import utils
from . import opt_check
from . import opt_download
from . import opt_upload
from . import opt_delete


def resolve_cwd(args: argparse.Namespace) -> str:
    """
    Determina la carpeta de trabajo a utilizar.
    """
    cwd = args.cwd
    if cwd == None or cwd == "":
        return "."
    else:
        return cwd.strip()


def resolve_aws_profile(args: argparse.Namespace) -> str:
    """
    Determina el perfil AWS a utilizar para ciertas operaciones que lo requieren. Imprime advertencias si es necesario.
    """
    # Resolver perfil aws. Si no se indica, se utiliza "default".
    profile = args.aws_profile
    if profile == None or profile == "":
        profile = "default"
        print(utils.bcolors.WARNING + "Advertencia: utilizando perfil por defecto \"default\"." + utils.bcolors.ENDC)
    else:
        print("{0}Utilizando perfil \"{1}\".{2}".format(utils.bcolors.OKBLUE, profile, utils.bcolors.ENDC))
    return profile.strip()


def resolve_aws_region(args: argparse.Namespace) -> str:
    """
    Determina la region AWS a utilizar para ciertas operaciones que lo requieren, si hubiere.
    """
    # Resolver región aws.
    region = args.aws_region
    if region == None or region == "":
        return ""
    else:
        region = region.strip()

    if region != "":
        print("{0}Utilizando región \"{1}\".{2}".format(utils.bcolors.OKBLUE, region, utils.bcolors.ENDC))

    return region


def resolve_secret_name(args: argparse.Namespace, msg: str) -> str:
    """
    Determina el valor de secreto AWS indicado.
    """
    # Resolver perfil aws. Si no se indica, se utiliza "default".
    secret_name = args.aws_secret
    if secret_name == None or secret_name == "":
        print(utils.bcolors.FAIL + msg + utils.bcolors.ENDC)
        exit(1)
    return secret_name


def main() -> None:
    """
    Implementa la lógica central de la herramienta.
    """
    parser = argparse.ArgumentParser(prog="aws_secrets_fs", description="Herramienta que permite sincronizar archivos con datos sensibles, utilizando AWS Secrets Manager como backend.")
    parser.add_argument('--action', type=str, required=True, choices=["check", "download", "upload", "delete"], help="Acción a realizar.")
    parser.add_argument("--cwd", type=str, required=False, help="Carpeta de trabajo para ciertas acciones que lo requieran.")
    parser.add_argument("--aws-profile", type=str, required=False, help="Nombre del perfil AWS configurado.")
    parser.add_argument("--aws-region", type=str, required=False, help="Nombre de región de preferencia para AWS.")
    parser.add_argument("--aws-secret", type=str, required=False, help="Nombre o ARN de secreto a procesar dependiendo de la acción indicada.")
    args = parser.parse_args()

    if args.action == "check":
        opt_check.run()

    if args.action == "download":
        cwd = resolve_cwd(args)
        profile = resolve_aws_profile(args)
        region = resolve_aws_region(args)
        opt_download.run(cwd, profile, region)

    if args.action == "upload":
        cwd = resolve_cwd(args)
        profile = resolve_aws_profile(args)
        region = resolve_aws_region(args)
        opt_upload.run(cwd, profile, region)

    if args.action == "delete":
        secret_name = resolve_secret_name(args, "Error: se debe especificar el secreto a procesar (--aws-secret).")
        profile = resolve_aws_profile(args)
        region = resolve_aws_region(args)
        opt_delete.run(secret_name, profile, region)
