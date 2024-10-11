import json
import os
import base64
from . import utils
from . import aws


def run(profile: str, region: str) -> None:
    """
    Procesa las entradas en archivos tipo descriptor y se encarga de recrear el contenido de los archivos indicados.
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
            print("\n" + utils.bcolors.OKGREEN + "Descargando: " + entry.filename + utils.bcolors.ENDC)

            # Descargar archivo de indice desde secrets manager.
            indexname = entry.secretname + ".index"
            print("Obteniendo índice: " + indexname)
            value, err = aws.retrieve_secret(indexname, profile, region)
            if err != None:
                print("Error: " + str(err))
                print(utils.bcolors.FAIL + "Error: no se pudo descargar el archivo índice." + utils.bcolors.ENDC)
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
                part_value, part_err = aws.retrieve_secret(partname, profile, region)
                if part_err != None:
                    print("Error: " + str(part_err))
                    partsok = False
                    break

                # Acumular partes en buffer.
                partsbuff.append(part_value)

            # Control.
            if partsok is False:
                print(utils.bcolors.FAIL + "Error: no se pudo descargar el archivo." + utils.bcolors.ENDC)
                continue

            # Recrear archivo.
            targetfile = os.path.join(".", entry.filename)
            if (os.path.exists(targetfile)):
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
                print(utils.bcolors.FAIL + "Error: no se pudo escribir el archivo." + utils.bcolors.ENDC)
                continue

            # Comprobación de contenido escrito.
            target = value["hash"]
            effective = utils.hash_file(targetfile)
            if target == effective:
                print("Comprobación: ok.")
            else:
                print("Comprobación: ko.")
