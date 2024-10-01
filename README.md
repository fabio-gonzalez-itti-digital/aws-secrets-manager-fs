# AWS Secrets Manager FS
Herramienta que permite sincronizar archivos con datos sensibles, utilizando AWS Secrets Manager como backend.

## Requerimientos
- Python 3.
- Boto 3, versión `1.34.120` o superior.
- AWS CLI, versión `2.x.x` o superior.

## Instalación
TBD

## Modo de Uso
La herramienta permite subir/descargar archivos utilizando AWS Secrets Manager como backend. Los archivos involucrados se indican a través de archivos descriptores que asocian nombres de archivos locales con secretos en AWS Secret Manager.

### Perfiles AWS
Antes que nada, se debe configurar al menos un perfil AWS a manera que la herramienta pueda utilizar las credenciales asociadas para acceder al API de AWS Secrets Manager. Para verificar que se cumple con este requerimiento podemos ejecutar la comprobación de la siguiente manera:

```
aws_secrets_fs --action check
```

Se listará en pantalla la versión de AWS Cli detectada y los perfiles configurados.

### Archivos Descriptores
Archivos de texto plano con extensión `.aws_fs_descriptor` que contienen pares clave+valor separados por `=>`. Cada par de datos especifica un nombre de archivo local y su mapeo a un secreto en AWS Secrets Manager. Ej.:

```
archivoA => /secrets/A
archivoB => /secrets/B
```

Cada archivo descriptor permite manipular archivos dentro de la carpeta actual contenedora del archivo descriptor. Pueden existir varios archivos descriptores en una misma carpeta y también varios archivos descriptores en varias otras carpetas de nuestro proyecto.

### Subir Archivos
Para subir un archivo local a Secrets Manager, debemos crear el archivo descriptor correspondiente y ejecutar la acción `upload` indicando el perfil AWS a utilizar. Si contamos con la siguiente estructura de carpetas y archivos:

```
/my_app
├── /config
│   └── /php
│       ├── config.inc.php
│       └── db.inc.php
├── /docker
│   ├── Dockerfile
│   └── docker-compose.yml
└── /src
    ├── /vendor
    │   ├── dep1.php
    │   └── dep2.php
    └── index.php
```

Donde `config.inc.php` y `db.inc.php` contienen datos sensibles que no deben ser versionados. Entonces procedemos a crear el archivo `configs.aws_fs_descriptor` en la carpeta `/my_app/config/php` con el siguiente contenido:

```
config.inc.php => /my_app/dev/config.inc.php
db.inc.php => /my_app/dev/db.inc.php
```

Procedemos a subir el contenido sensible a Secrets Manager con la acción `upload` indicando el perfil AWS a utilizar:

```
aws_secrets_fs --action upload --aws_profile <profile>
```

Si todo está correcto, los archivos locales estarán almacenados en AWS Secrets Manager y pueden ser eliminados del entorno local para luego proceder a versionar el archivo descriptor. De esta manera, no se compromete el contenido de carácter sensible de los archivos y se mantiene un seguimiento de cambios a través de los archivos descriptores.

> Observación: Cada subida de archivos reemplaza cualquier otro valor existente en secrets manager. Se debe tener especial cuidado cuando varios usuarios diferentes pueden editar y actualizar el mismo archivo.

### Descargar Archivos
En el proceso inverso a la subida de archivos, siguiendo el ejemplo anterior tendriamos la siguiente jerarquía de carpetas y archivos una vez clonado el repositorio:

```
/my_app
├── /config
│   └── /php
│       └── configs.aws_fs_descriptor
├── /docker
│   ├── Dockerfile
│   └── docker-compose.yml
└── /src
    ├── /vendor
    │   ├── dep1.php
    │   └── dep2.php
    └── index.php
```

Para recuperar nuestros archivos sensibles, basta con ejecutar la acción `download` de la herramienta indicando de igual forma el perfil AWS a utilizar.

```
cd /my_app/config/php
aws_secrets_fs --action download --aws_profile <profile>
```

> Observación: Cada descarga de archivos reemplaza cualquier archivo local que se encuentre. Si los archivos tienen cambios locales, estos se perderan.

## Mejoras a Futuro
- Implementar eliminación de archivos/secretos. De momento esto se hace manualmente desde la consola AWS.
- Dar soporte a otros tipos de identidad AWS.
- Dar soporte a archivos binarios.
- Dar soporte para colisiones de nombres de archivo entre entornos diferentes de una misma cuenta AWS.