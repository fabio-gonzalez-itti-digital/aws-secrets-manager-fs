import argparse
import shutil
import subprocess

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def opt_check():
    # Verificar si aws cli esta disponible.
    command = shutil.which("aws")
    if command == None or command == "":
        print(bcolors.FAIL + "Error: No se encontró AWS CLI." + bcolors.ENDC)
        exit(1)

    # Versión de aws cli.
    aws_version = ""
    out = subprocess.check_output(['aws', '--version'])
    if out == None or out == '':
        print(bcolors.FAIL + "Error: No se pudo determinar la versión de AWS CLI." + bcolors.ENDC)
    else:
        aws_version = out.decode("utf-8").strip().split(" ")[0].split("/")[1]
    print("AWS CLI Version: {0}{1}{2}".format(bcolors.OKGREEN, aws_version, bcolors.ENDC))

    # Listar perfiles disponibles.
    aws_profiles = list()
    out = subprocess.check_output(['aws', 'configure', 'list-profiles'])
    if out != None:
        tmp = out.decode("utf-8").split('\n')
        for t in tmp:
            if t != None:
                t = t.strip()
                if t != "":
                    aws_profiles.append(t)
    print("AWS CLI Profiles {0}({1}){2}:".format(bcolors.OKGREEN, len(aws_profiles), bcolors.ENDC))
    for aws_profile in aws_profiles:
        print("  • {0}".format(aws_profile))

def main():
    parser = argparse.ArgumentParser(prog="aws_secrets_fs", description="Herramienta que permite sincronizar archivos con datos sensibles, utilizando AWS Secrets Manager como backend.")
    parser.add_argument('--action', type=str, required=True, choices=["check", "download", "upload", "view"], help="Acción a realizar.")
    parser.add_argument("--aws_profile", type=str, required=False, help="Nombre del perfil AWS configurado.")
    args = parser.parse_args()

    if args.action == "check":
        opt_check()

if __name__ == '__main__':
    main()