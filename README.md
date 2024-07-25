# Download Flowpaper

## Descripción
Este programa convierte todas las imágenes en una carpeta específica en un archivo PDF. Soporta imágenes en formato PNG, JPG y JPEG. Puede funcionar con parámetros proporcionados individualmente o a través de un archivo CSV.

## Requisitos
* Python 3.x
* Librerías:
    * Pillow
    * reportlab

## Instalación
1) Clonar el repositorio o descargar los archivos.
2) Instalar las dependencias necesarias:
    ``pip install pillow reportlab``

## Uso
El programa puede ejecutarse proporcionando parámetros individuales o un archivo CSV que contenga múltiples configuraciones.

### Uso con Parámetros Individuales
``python convert_images_to_pdf.py --folder_path <ruta_a_la_carpeta> --pdf_name <nombre_del_pdf> ``
* --folder_path: Carpeta que contiene las imágenes a incluir en el PDF.
* --pdf_name: Nombre del archivo PDF resultante.
### Uso con Archivo CSV
``python convert_images_to_pdf.py --csv_file <ruta_al_csv>``
* --csv_file: Archivo CSV que contiene las rutas de las carpetas y los nombres de los archivos PDF.
El archivo CSV debe tener el siguiente formato:

````csv
ruta_a_la_carpeta_1;nombre_del_pdf_1
ruta_a_la_carpeta_2;nombre_del_pdf_2
...
````