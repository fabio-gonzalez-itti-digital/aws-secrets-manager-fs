import hashlib
import os


class bcolors:
    """
    Constantes para utilización de códigos de escape POSIX en salida estándar.
    Attributes:
        ENDC: Código de escape para fin de formateo.
        HEADER: Código de escape para indicar de texto en negrita.
        OKBLUE: Código de escape para inidicar estado de éxito utilizando color azul.
        OKCYAN: Código de escape para inidicar estado de éxito utilizando color cyan.
        OKGREEN: Código de escape para inidicar estado de éxito utilizando color verde.
        WARNING: Código de escape para indicar estado de advertencia.
        WARNING: Código de escape para indicar estado de fallo.
        BOLD: Código de escape para indicar de texto en negrita.
        UNDERLINE: Código de escape para indicar texto subrayado.
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
    Attributes:
        filename: nombre para archivo en sistema de archivos local.
        secretname: nombre para secreto en Secrets Manager.
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


def get_descriptor_files(path: str) -> list[str]:
    """
    Obtiene la lista de archivos de tipo descriptor. Archivos con extensión: .aws_secrets.
    Parameters:
        path: Path donde buscar los archivos de tipo descriptor.
    """
    filepaths = list()
    for filepath in os.listdir(path):
        if filepath.endswith(".aws_secrets"):
            p = os.path.join(path, filepath).strip()
            filepaths.append(p)
    return filepaths


def parse_descriptor_file(path: str) -> list[DescriptorFileEntry]:
    """
    Parsea el contenido de un archivo de tipo descriptor y retorna las entradas encontradas.
    Parameters:
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
