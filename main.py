import argparse
import shutil
import subprocess
import os
import json
import hashlib
import base64
from botocore.exceptions import ClientError
import aws

class bcolors:
    """
    Constantes para utilización de colores POSIX en salida estándar.
    """
    ENDC = '\033[0m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DescriptorFileEntry:
    """
    Entrada de un archivo de tipo descriptor.
    """
    filename = ""
    secretname = ""

    def __init__(self, filename, secretname):
        """
        Constructor
        """
        self.filename = filename
        self.secretname = secretname

    def __repr__(self):
        """
        Retorna la representación en forma de texto para instancias de esta clase.
        """
        return "[{0} → {1}]".format(self.filename, self.secretname)


def opt_check() -> None:
    """
    Verifica las dependencias necesarias. De momento, que esté instalado aws cli.
    Se imprime la versión encontrada y los perfiles configurados.
    """
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
        exit(1)
    aws_version = out.decode("utf-8").strip().split(" ")[0].split("/")[1]
    print("AWS CLI Version: {0}{1}{2}".format(bcolors.OKGREEN, aws_version, bcolors.ENDC))

    # Listar perfiles disponibles.
    aws_profiles = list()
    try:
        # NOTE: aws configure list-profiles existe a partir de la versión 2.x.x.
        out = subprocess.check_output(['aws', 'configure', 'list-profiles'])
        if out != None:
            lines = out.decode("utf-8").split('\n')
            for line in lines:
                if line != None:
                    line = line.strip()
                    if line != "":
                        aws_profiles.append(line)
        print("AWS CLI Profiles {0}({1}){2}:".format(bcolors.OKGREEN, len(aws_profiles), bcolors.ENDC))
        for aws_profile in aws_profiles:
            print("  • {0}".format(aws_profile))
    except Exception:
        print(bcolors.WARNING + "Advertencia: \"aws configure list-profiles\" no soportado." + bcolors.ENDC)


def get_descriptor_files(path: str) -> list[str]:
    """
    Obtiene la lista de archivos de tipo descriptor. Archivos con extensión: .aws_fs_descriptor.
    path: Path donde buscar los archivos de tipo descriptor.
    """
    filepaths = list()
    for filepath in os.listdir(path):
        if filepath.endswith(".aws_fs_descriptor"):
            p = os.path.join(path, filepath).strip()
            filepaths.append(p)
    return filepaths


def parse_descriptor_file(path: str) -> list[DescriptorFileEntry]:
    """
    Parsea el contenido de un archivo de tipo descriptor y retorna las entradas encontradas.
    path: Path de archivo tipo descriptor.
    """
    entries = list()
    with open(path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line != "" and line.startswith("#") is False:
                a, b = line.split("=>")
                entry = DescriptorFileEntry(a.strip(), b.strip())
                entries.append(entry)
    return entries

def hash_file(path: str) -> str:
    """
    Obtiene el valor de hash md5 para un archivo dado.
    """
    BUF_SIZE = 65536
    md5 = hashlib.md5()
    with open(path, 'rb') as file:
        while True:
            data = file.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def opt_download(profile: str) -> None:
    """
    Procesa las entradas en archivos tipo descriptor y se encarga de recrear el contenido de los archivos indicados.
    profile: Perfil aws a utilizar.
    """
    # Obtener descriptores en carpeta actual.
    descriptors = get_descriptor_files(".")
    if (len(descriptors) == 0):
        print("No se encontraron archivos descriptores.")
        exit(1)

    # Extraer entradas de cada archivo descriptor.
    for descriptor in descriptors:
        entries = parse_descriptor_file(descriptor)
        for entry in entries:
            print("\n" + bcolors.OKGREEN + "Descargando: " + entry.filename + bcolors.ENDC)

            # Descargar archivo de indice desde secrets manager.
            indexname = entry.secretname + ".index"
            print("Obteniendo índice: " + indexname)
            value, err = aws.retrieve_secret(indexname, profile)
            if err != None:
                print("Error: " + str(err))
                print(bcolors.FAIL + "Error: no se pudo descargar el archivo índice." + bcolors.ENDC)
                continue

            # El valor del indice es un json con los siguientes campos:
            # - hash: hash sha256 de archivo completo.
            # - parts: cantidad de partes en la que se divide el archivo.
            print("Archivo índice: ok.")
            value = json.loads(value)

            # Descargar partes.
            partsnum = value["parts"]
            partsok = True
            partsbuff = list()
            for i in range(partsnum):
                print("Descargando parte: {0}/{1}".format(i+1, partsnum))
                partname = entry.secretname + ".{0}".format(i)
                part_value, part_err = aws.retrieve_secret(partname, profile)
                if part_err != None:
                    print("Error: " + str(part_err))
                    partsok = False
                    break

                # Acumular partes en buffer.
                partsbuff.append(part_value)

            # Control.
            if partsok is False:
                print(bcolors.FAIL + "Error: no se pudo descargar el archivo." + bcolors.ENDC)
                continue

            # Recrear archivo.
            targetfile = os.path.join(".", entry.filename)
            if(os.path.exists(targetfile)):
                print("Sobreescribiendo archivo ...")
            else:
                print("Creando archivo ...")

            # Escritura de contenido.
            try:
                with open(targetfile, "w", encoding="utf-8") as file:
                    for partsbuff_entry in partsbuff:
                        # Decodificar desde base64.
                        plain = base64.b64decode(partsbuff_entry).decode("utf-8")
                        file.write(plain)
                        file.flush()
                print("Escritura: ok.")
            except Exception as e:
                print("Error: " + str(e))
                print(bcolors.FAIL + "Error: no se pudo escribir el archivo." + bcolors.ENDC)
                continue

            # Comprobación de contenido escrito.
            target = value["hash"]
            effective = hash_file(targetfile)
            if target == effective:
                print("Comprobación: ok.")
            else:
                print("Comprobación: ko.")

def opt_upload(profile):
    """
    Procesa las entradas en archivos tipo descriptor y se encarga de subir el contenido de los archivos indicados y asociarlos
    a un secreto de aws secrets manager.
    profile: Perfil aws a utilizar.
    """
    # Obtener descriptores en carpeta actual.
    descriptors = get_descriptor_files(".")
    if (len(descriptors) == 0):
        print("No se encontraron archivos descriptores.")
        exit(1)

    # Extraer entradas de cada archivo descriptor.
    for descriptor in descriptors:
        entries = parse_descriptor_file(descriptor)
        for entry in entries:
            print("\n" + bcolors.OKGREEN + "Subiendo: " + entry.filename + bcolors.ENDC)

            # El archivo debe existir.
            targetfile = os.path.join(".", entry.filename)
            if(os.path.exists(targetfile) == False):
                print(bcolors.FAIL + "Error: el archivo no existe." + bcolors.ENDC)
                continue

            # Calcular hash md5 de archivo.
            print("Calculando valor de comprobación ...")
            hash_md5 = ""
            try:
                hash_md5 = hash_file(targetfile)
            except Exception as e:
                print("Error: " + str(e))
                print(bcolors.FAIL + "Error: no se pudo calcular el valor de comprobación." + bcolors.ENDC)
                continue

            # Codificar contenido en base64 y separar en chunks.
            # NOTE: Cada chunk contiene 50kb de contenido en base64. El valor
            # máximo a la fecha para un secret es de 64kb.
            print("Calculando partes ...")
            CHUNK_SIZE = 50 * 1024
            chunks = list()
            try:
                with open(targetfile, "rb") as file:
                    b64 = base64.b64encode(file.read()).decode("utf-8")
                    for i in range(0, len(b64), CHUNK_SIZE):
                        chunks.append(b64[i : i + CHUNK_SIZE])
            except Exception as e:
                print("Error: " + str(e))
                print(bcolors.FAIL + "Error: no se pudieron calcular las partes del archivo." + bcolors.ENDC)
                continue

            # Crear indice.
            print("Creando archivo índice ...")
            try:
                value = {
                    "v": 1,
                    "hash": hash_md5,
                    "parts": len(chunks)
                }
                value = json.dumps(value)
                indexname = entry.secretname + ".index"
                response, err = aws.update_secret(indexname, value, profile)
                if err != None and isinstance(err, ClientError):
                    response, err = aws.create_secret(indexname, value, profile)
                if err != None:
                    raise err
                print("Archivo índice: ok.")
            except Exception as e:
                print("Error: " + str(e))
                print(bcolors.FAIL + "Error: no se puedo crear el archivo índice." + bcolors.ENDC)
                continue

            # Crear partes.
            i = 0
            for chunk in chunks:
                print("Subiendo parte: {0}/{1}".format(i + 1, len(chunks)))
                try:
                    # Crear parte.
                    partname = entry.secretname + ".{0}".format(i)
                    response, err = aws.update_secret(partname, chunk, profile)
                    if err != None and isinstance(err, ClientError):
                        response, err = aws.create_secret(partname, chunk, profile)
                    if err != None:
                        raise err
                except Exception as e:
                    print("Error: " + str(e))
                    print(bcolors.FAIL + "Error: no se puedo subir la parte calculada." + bcolors.ENDC)
                    continue

                # Siguiente numero de parte.
                i = i + 1

def resolve_aws_profile(args: any) -> str:
    """
    Determina el perfil AWS a utilizar para ciertas operaciones que lo requieren. Imprime advertencias si es necesario.
    """
    # Resolver perfil aws. Si no se indica, se utiliza "default".
    profile = args.aws_profile
    if profile == None or profile == "":
        profile = "default"
        print(bcolors.WARNING + "Advertencia: utilizando perfil por defecto \"default\"." + bcolors.ENDC)
    else:
        print("{0}Utilizando perfil \"{1}\".{2}".format(bcolors.OKBLUE, profile, bcolors.ENDC))
    return profile

def main() -> None:
    """
    Implementa la lógica central de la herramienta.
    """
    parser = argparse.ArgumentParser(prog="aws_secrets_fs", description="Herramienta que permite sincronizar archivos con datos sensibles, utilizando AWS Secrets Manager como backend.")
    parser.add_argument('--action', type=str, required=True, choices=["check", "download", "upload"], help="Acción a realizar.")
    parser.add_argument("--aws_profile", type=str, required=False, help="Nombre del perfil AWS configurado.")
    args = parser.parse_args()

    if args.action == "check":
        # Operar.
        opt_check()

    if args.action == "download":
        # Operar.
        profile = resolve_aws_profile(args)
        opt_download(profile)

    if args.action == "upload":
        # Operar.
        profile = resolve_aws_profile(args)
        opt_upload(profile)


if __name__ == '__main__':
    main()
