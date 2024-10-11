import os
import json
import base64
from botocore.exceptions import ClientError
from . import utils
from . import aws


def run(profile: str, region: str):
    """
    Procesa las entradas en archivos tipo descriptor y se encarga de subir el contenido de los archivos indicados y asociarlos
    a un secreto de aws secrets manager.
    Parameters:
        profile: Perfil aws a utilizar.
        region: Región aws a utilizar, si hubiere.
    """
    # Obtener descriptores en carpeta actual.
    descriptors = utils.get_descriptor_files(".")
    if (len(descriptors) == 0):
        print("No se encontraron archivos descriptores.")
        exit(1)

    # Extraer entradas de cada archivo descriptor.
    for descriptor in descriptors:
        entries = utils.parse_descriptor_file(descriptor)
        for entry in entries:
            print("\n" + utils.bcolors.OKGREEN + "Subiendo: " + entry.filename + utils.bcolors.ENDC)

            # El archivo debe existir.
            targetfile = os.path.join(".", entry.filename)
            if (os.path.exists(targetfile) == False):
                print(utils.bcolors.FAIL + "Error: el archivo no existe." + utils.bcolors.ENDC)
                continue

            # Calcular hash md5 de archivo.
            print("Calculando valor de comprobación ...")
            hash_md5 = ""
            try:
                hash_md5 = utils.hash_file(targetfile)
            except Exception as e:
                print("Error: " + str(e))
                print(utils.bcolors.FAIL + "Error: no se pudo calcular el valor de comprobación." + utils.bcolors.ENDC)
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
                        chunks.append(b64[i: i + CHUNK_SIZE])
            except Exception as e:
                print("Error: " + str(e))
                print(utils.bcolors.FAIL + "Error: no se pudieron calcular las partes del archivo." + utils.bcolors.ENDC)
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
                _, err = aws.update_secret(indexname, value, profile, region)
                if err != None and isinstance(err, ClientError):
                    _, err = aws.create_secret(indexname, value, profile, region)
                if err != None:
                    raise err
                print("Archivo índice: ok.")
            except Exception as e:
                print("Error: " + str(e))
                print(utils.bcolors.FAIL + "Error: no se puedo crear el archivo índice." + utils.bcolors.ENDC)
                continue

            # Crear partes.
            i = 0
            for chunk in chunks:
                print("Subiendo parte: {0}/{1}".format(i + 1, len(chunks)))
                try:
                    # Crear parte.
                    partname = entry.secretname + ".{0}".format(i)
                    _, err = aws.update_secret(partname, chunk, profile, region)
                    if err != None and isinstance(err, ClientError):
                        _, err = aws.create_secret(partname, chunk, profile, region)
                    if err != None:
                        raise err
                except Exception as e:
                    print("Error: " + str(e))
                    print(utils.bcolors.FAIL + "Error: no se puedo subir la parte calculada." + utils.bcolors.ENDC)
                    continue

                # Siguiente numero de parte.
                i = i + 1
