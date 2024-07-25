import os
import time
import shutil
import csv
import argparse
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from PIL import Image, ImageOps
from io import BytesIO

# Constantes para la captura de imágenes
TOP = 63
LEFT = 704
BOTTOM = 1781
RIGHT = 3136
SPLIT_HEIGHT = (RIGHT - LEFT) / 2
PAGE_LEFT = (LEFT, TOP, LEFT + SPLIT_HEIGHT, BOTTOM)
PAGE_RIGHT = (LEFT + SPLIT_HEIGHT, TOP, RIGHT, BOTTOM)
BORDER_SIZE = 50
IMAGE_QUALITY = 85  # Ajusta la calidad de las imágenes JPEG

def load_config(config_file: str) -> dict:
    """
    Carga las configuraciones desde un archivo YAML.

    :param config_file: Ruta al archivo de configuración YAML.
    :type config_file: str
    :return: Diccionario de configuraciones.
    :rtype: dict
    """
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def parse_arguments() -> argparse.Namespace:
    """
    Analiza los argumentos de la línea de comandos.

    :return: Argumentos analizados.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Captura y procesa imágenes de un Flipbook.")
    parser.add_argument('--url', type=str, help='La URL del Flipbook')
    parser.add_argument('--iterations', type=int, help='Número de iteraciones de clic')
    parser.add_argument('--folder', type=str, help='Carpeta para guardar las imágenes')
    parser.add_argument('--csv_file', type=str, help='Archivo CSV que contiene URL, iteraciones y carpeta')
    return parser.parse_args()

def setup_folder(folder: str) -> None:
    """
    Configura la carpeta para guardar las imágenes, creando una nueva o eliminando la existente.

    :param folder: Ruta a la carpeta.
    :type folder: str
    :return: None
    """
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)

def configure_browser(chromedriver_path: str) -> webdriver.Chrome:
    """
    Configura y devuelve un navegador Chrome sin cabeza.

    :param chromedriver_path: Ruta al archivo ejecutable de ChromeDriver.
    :type chromedriver_path: str
    :return: Navegador Chrome configurado.
    :rtype: webdriver.Chrome
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-3d-apis")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(3840, 2160)
    return driver

def remove_page_padding(driver: webdriver.Chrome) -> None:
    """
    Elimina el relleno superior del contenedor de las páginas en el Flipbook.

    :param driver: Instancia del navegador Chrome.
    :type driver: webdriver.Chrome
    :return: None
    """
    element = driver.find_element(By.ID, "pagesContainer_documentViewer_parent")
    driver.execute_script("""
        var element = arguments[0];
        var style = element.getAttribute('style');
        if (style) {
            var styles = style.split(';');
            var newStyle = styles.filter(function(s) {
                return !s.trim().startsWith('padding-top:');
            }).join(';').trim();
            element.setAttribute('style', newStyle);
        }
    """, element)

def remove_fisheye(driver: webdriver.Chrome) -> None:
    """
    Elimina el efecto de ojo de pez del visor del Flipbook.

    :param driver: Instancia del navegador Chrome.
    :type driver: webdriver.Chrome
    :return: None
    """
    element = driver.find_element(By.CLASS_NAME, "flowpaper_fisheye")
    driver.execute_script("""
        var element = arguments[0];
        if (element) {
            element.parentNode.removeChild(element);
        }
    """, element)

def replace_borders_with_white(image: Image.Image, border_size: int) -> Image.Image:
    """
    Reemplaza los bordes izquierdo y derecho de la imagen con una franja blanca del tamaño especificado.

    :param image: Imagen original.
    :type image: Image.Image
    :param border_size: Tamaño del borde en píxeles.
    :type border_size: int
    :return: Imagen con bordes reemplazados por blanco.
    :rtype: Image.Image
    """
    width, height = image.size
    new_width = width - 2 * border_size

    # Crear una nueva imagen con el tamaño deseado (sin bordes)
    new_image = Image.new("RGB", (new_width, height), "white")

    # Recortar la imagen original para eliminar los bordes
    cropped_image = image.crop((border_size, 0, width - border_size, height))

    # Insertar la imagen recortada en la nueva imagen con bordes blancos
    new_image.paste(cropped_image, (0, 0))

    return new_image

def reduce_image_size(image: Image.Image) -> Image.Image:
    """
    Redimensiona la imagen para ajustarla a las dimensiones de A4 mientras mantiene la relación de aspecto.

    :param image: La imagen a redimensionar.
    :type image: Image.Image
    :return: Imagen redimensionada.
    :rtype: Image.Image
    """
    width, height = image.size
    a4_width, a4_height = 2480, 3508  # Dimensiones A4 en píxeles a 300 DPI
    aspect_ratio = width / height

    if width > a4_width or height > a4_height:
        if aspect_ratio > 1:  # Más ancha que alta
            new_width = a4_width
            new_height = int(a4_width / aspect_ratio)
        else:  # Más alta que ancha
            new_height = a4_height
            new_width = int(a4_height * aspect_ratio)

        image = image.resize((new_width, new_height), Image.LANCZOS)

    return image

def capture_and_save_images(driver: webdriver.Chrome, actions: ActionChains, folder: str, iterations: int) -> None:
    """
    Captura capturas de pantalla del Flipbook y las guarda como imágenes.

    :param driver: Instancia del navegador Chrome.
    :type driver: webdriver.Chrome
    :param actions: Instancia de ActionChains para realizar acciones.
    :type actions: ActionChains
    :param folder: Carpeta para guardar las imágenes.
    :type folder: str
    :param iterations: Número de iteraciones para capturar imágenes.
    :type iterations: int
    :return: None
    """
    for i in range(iterations):
        time.sleep(3.5)
        act_page = i * 2 + 1
        next_page = i * 2 + 2
        png = driver.get_screenshot_as_png()
        full_image = Image.open(BytesIO(png))
        region_left = full_image.crop(PAGE_LEFT)
        region_right = full_image.crop(PAGE_RIGHT)

        # Reemplazar los bordes y reducir el tamaño de la imagen
        img_left = replace_borders_with_white(reduce_image_size(region_left), BORDER_SIZE)
        img_right = replace_borders_with_white(reduce_image_size(region_right), BORDER_SIZE)

        img_left.save(os.path.join(folder, f"pag_{act_page}.jpg"), format="JPEG", quality=IMAGE_QUALITY)
        img_right.save(os.path.join(folder, f"pag_{next_page}.jpg"), format="JPEG", quality=IMAGE_QUALITY)
        actions.click().perform()

def process_single_url(url: str, iterations: int, folder: str, chromedriver_path: str) -> None:
    """
    Procesa una URL de Flipbook, capturando y guardando imágenes.

    :param url: URL del Flipbook.
    :type url: str
    :param iterations: Número de iteraciones para capturar imágenes.
    :type iterations: int
    :param folder: Carpeta para guardar las imágenes.
    :type folder: str
    :param chromedriver_path: Ruta al archivo ejecutable de ChromeDriver.
    :type chromedriver_path: str
    :return: None
    """
    setup_folder(folder)
    driver = configure_browser(chromedriver_path)
    driver.get(url)
    time.sleep(3)
    remove_page_padding(driver)
    remove_fisheye(driver)
    actions = ActionChains(driver)
    actions.move_by_offset(3150, 930)
    capture_and_save_images(driver, actions, folder, iterations)
    driver.quit()

def main() -> None:
    """
    Función principal para ejecutar el script.

    :return: None
    """
    args = parse_arguments()
    config = load_config('config.yaml')

    if args.csv_file:
        with open(args.csv_file, newline='') as file:
            reader = csv.reader(file, delimiter=';')
            for row in reader:
                url, iterations, folder = row
                process_single_url(url, int(iterations), folder, config['paths']['chromedriver_path'])
    elif args.url and args.iterations and args.folder:
        process_single_url(args.url, args.iterations, args.folder, config['paths']['chromedriver_path'])
    else:
        print("Error: Debe proporcionar o bien el CSV o los parámetros individuales --url, --iterations y --folder.")

if __name__ == "__main__":
    main()
