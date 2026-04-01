import os
import urllib.parse
import threading
import socketserver
from http.server import SimpleHTTPRequestHandler
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Configuración de directorios y servidor
DIR_P3 = 'petcare-frontend'
DIR_P2 = 'other/input'
DIR_OUT_MAPAS = 'doc/mapasDeEtiquetas'
DIR_OUT_CAPTURAS = 'doc/capturas_responsivas'
PUERTO = 8088

ETIQUETAS_BLOQUE = {
    'main', 'header', 'footer', 'nav', 'aside', 'section', 'article',
    'div', 'form', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd', 'figure', 'figcaption', 'details',
    'dialog', 'address', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p',
    'blockquote', 'fieldset', 'legend', 'search', 'menu'
}

ETIQUETAS_ELIMINAR = {
    'head', 'script', 'style', 'meta', 'link', 'noscript', 'template',
    'iframe', 'object', 'embed', 'svg', 'canvas', 'video', 'audio', 'img'
}

ESTILOS_BOXMODEL = """
    head, meta, title, link, script, style, img, svg { display: none !important; }
    body { font-family: monospace; background: #f4f4f4; padding: 20px; margin: 0; }
    *[data-etiqueta] {
        border: 2px solid #2c3e50;
        padding: 10px;
        margin: 10px;
        display: block;
        background: white;
        position: relative;
        min-height: 20px;
    }
    *[data-etiqueta]::before {
        content: attr(data-etiqueta);
        display: block;
        background: #2c3e50;
        color: white;
        padding: 4px 8px;
        font-size: 14px;
        font-weight: bold;
        width: fit-content;
        margin-bottom: 8px;
    }
    *[data-etiqueta][id]::before {
        content: attr(data-etiqueta) " #" attr(id) !important;
    }
"""

# Implementación de servidor local que suprime logs estándar
class ManejadorSilencioso(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

class ServidorTCPReutilizable(socketserver.TCPServer):
    allow_reuse_address = True

def limpiar_atributos_html(soup):
    """Elimina todos los atributos excepto 'id' de cada etiqueta HTML."""
    for tag in soup.find_all(True):
        atributos_a_borrar = [attr for attr in tag.attrs if attr != 'id']
        for attr in atributos_a_borrar:
            del tag[attr]

def limpiar_y_preparar_arbol(soup):
    for tag in soup.find_all(list(ETIQUETAS_ELIMINAR)):
        tag.decompose()

    for tag in reversed(soup.find_all(True)):
        if tag.name not in ETIQUETAS_BLOQUE and tag.name not in ['html', 'body']:
            if tag.parent is not None:
                tag.unwrap()

def aplicar_formato_cajas(soup):
    for tag in soup.find_all(True):
        if tag.name in ['html', 'body']:
            continue
        tag['data-etiqueta'] = tag.name
        tag.name = 'div'
        for text_node in tag.find_all(string=True, recursive=False):
            if text_node.strip():
                text_node.extract()

def capturar_pantalla(page, ruta_relativa, ruta_salida, viewport=None, full_page=True, ajustar_body=False):
    if viewport:
        page.set_viewport_size(viewport)
    else:
        page.set_viewport_size({"width": 1280, "height": 800})

    ruta_url = urllib.parse.quote(ruta_relativa.replace('\\', '/'))
    url_localhost = f"http://localhost:{PUERTO}/{ruta_url}"

    # networkidle asegura que Playwright espere a que finalicen las llamadas fetch de JSON/XML
    page.goto(url_localhost, wait_until='networkidle')

    if ajustar_body:
        elemento_cuerpo = page.locator("body")
        elemento_cuerpo.screenshot(path=ruta_salida)
    else:
        page.screenshot(path=ruta_salida, full_page=full_page)

def obtener_html_renderizado(page, directorio, archivo):
    """
    Navega a la página a través del servidor HTTP local y obtiene el HTML
    completamente renderizado por el motor JavaScript del navegador.
    Esto captura también los elementos inyectados dinámicamente (fetch JSON/XML, etc.).
    """
    ruta_relativa = os.path.join(directorio, archivo)
    ruta_url = urllib.parse.quote(ruta_relativa.replace('\\', '/'))
    url_localhost = f"http://localhost:{PUERTO}/{ruta_url}"
    page.set_viewport_size({"width": 1280, "height": 800})
    # networkidle garantiza que las peticiones de datos dinámicos hayan finalizado
    page.goto(url_localhost, wait_until='networkidle')
    return page.content()

def generar_mapas(archivo, page, directorio, sufijo_salida=''):
    """
    Genera mapas de etiquetas para un archivo HTML.

    Obtiene el DOM completamente renderizado (incluyendo contenido dinámico)
    a través del navegador en lugar de leer el archivo estático en disco.
    Los atributos 'id' se preservan y se muestran en la etiqueta del diagrama.

    Args:
        archivo: nombre del archivo HTML
        page: página de Playwright
        directorio: directorio desde el cual servir el archivo
        sufijo_salida: sufijo para añadir al nombre del archivo de salida antes de la extensión
    """
    nombre_base = archivo.replace('.html', '')

    # Obtener HTML renderizado dinámicamente en lugar de leer el fichero estático
    html_renderizado = obtener_html_renderizado(page, directorio, archivo)
    soup_web = BeautifulSoup(html_renderizado, 'html.parser')

    limpiar_y_preparar_arbol(soup_web)

    soup_normal = BeautifulSoup(str(soup_web), 'html.parser')
    # Conserva únicamente el atributo 'id'; el resto se elimina
    limpiar_atributos_html(soup_normal)
    aplicar_formato_cajas(soup_normal)

    estilo_tag = soup_normal.new_tag('style')
    estilo_tag.string = ESTILOS_BOXMODEL
    if not soup_normal.head:
        soup_normal.insert(0, soup_normal.new_tag('head'))
    soup_normal.head.append(estilo_tag)

    ruta_tmp_normal = os.path.join(DIR_OUT_MAPAS, f"{nombre_base}_tmp.html")
    with open(ruta_tmp_normal, 'w', encoding='utf-8') as f:
        f.write(str(soup_normal))

    # Nomenclatura: {nombre}-boxmodel.png / {nombre}-boxmodel-new.png
    nombre_salida = f"{nombre_base}-boxmodel{sufijo_salida}.png"
    capturar_pantalla(page, ruta_tmp_normal, os.path.join(DIR_OUT_MAPAS, nombre_salida), ajustar_body=True)
    os.remove(ruta_tmp_normal)

def generar_capturas_reales_responsivas(archivo, page, directorio):
    """
    Genera capturas responsivas para un archivo HTML.
    Se usa únicamente para los archivos actuales de petcare-frontend.
    Las dimensiones de viewport se ajustan a valores estándar reales
    y full_page=False garantiza que el tamaño de la imagen coincida
    exactamente con el del viewport simulado.

    Args:
        archivo: nombre del archivo HTML
        page: página de Playwright
        directorio: directorio desde el cual servir el archivo
    """
    nombre_base = archivo.replace('.html', '')
    ruta_relativa = os.path.join(directorio, archivo)

    # Dimensiones estándar ajustadas: evitan capturas desproporcionadas
    dispositivos = {
        'desktop': {'width': 1440, 'height': 900},
        'tablet':  {'width': 768,  'height': 1024},
        'mobile':  {'width': 390,  'height': 844},
    }

    for disp, viewport in dispositivos.items():
        nombre_fichero = f"{nombre_base}-{disp}.png"
        ruta_salida = os.path.join(DIR_OUT_CAPTURAS, nombre_fichero)
        capturar_pantalla(page, ruta_relativa, ruta_salida,
                          viewport=viewport, ajustar_body=False, full_page=False)

if __name__ == '__main__':
    os.makedirs(DIR_OUT_MAPAS, exist_ok=True)
    os.makedirs(DIR_OUT_CAPTURAS, exist_ok=True)

    print(f"Iniciando servidor local en el puerto {PUERTO}...")
    httpd = ServidorTCPReutilizable(("", PUERTO), ManejadorSilencioso)
    hilo_servidor = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo_servidor.start()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Mapas de etiquetas "antiguos" (other/input) — sin capturas responsivas
        archivos_antiguos = sorted(f for f in os.listdir(DIR_P2) if f.endswith('.html'))
        for archivo in archivos_antiguos:
            print(f"Procesando (antiguo) {archivo}...")
            generar_mapas(archivo, page, DIR_P2, sufijo_salida='')

        # 2. Mapas de etiquetas "actuales" + capturas responsivas (petcare-frontend)
        archivos_nuevos = sorted(f for f in os.listdir(DIR_P3) if f.endswith('.html'))
        for archivo in archivos_nuevos:
            print(f"Procesando (actual) {archivo}...")
            generar_mapas(archivo, page, DIR_P3, sufijo_salida='-new')
            generar_capturas_reales_responsivas(archivo, page, DIR_P3)

        browser.close()

    httpd.shutdown()
    httpd.server_close()
    print("\n¡Proceso completado con éxito! Revisa la carpeta doc/")
