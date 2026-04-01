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
    *[data-cambio="nuevo"] { border-color: #27ae60 !important; border-width: 3px !important; }
    *[data-cambio="nuevo"]::before { background: #27ae60 !important; content: attr(data-etiqueta) " (NUEVO)" !important; }
    *[data-cambio="atributos"] { border-color: #d35400 !important; border-style: dashed !important; border-width: 3px !important;}
    *[data-cambio="atributos"]::before { background: #d35400 !important; content: attr(data-etiqueta) " (ATRIBUTOS MODIFICADOS)" !important; }
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

def comparar_arboles(nodo_p2, nodo_p3):
    if not hasattr(nodo_p3, 'name') or nodo_p3.name is None:
        return

    if nodo_p2 is None:
        nodo_p3['data-cambio'] = 'nuevo'
        for child in nodo_p3.find_all(True):
            child['data-cambio'] = 'nuevo'
        return

    attrs_p2 = {k: v for k, v in nodo_p2.attrs.items() if k not in ['data-etiqueta', 'data-cambio']}
    attrs_p3 = {k: v for k, v in nodo_p3.attrs.items() if k not in ['data-etiqueta', 'data-cambio']}
    
    if attrs_p2 != attrs_p3:
        nodo_p3['data-cambio'] = 'atributos'

    hijos_p2 = [c for c in nodo_p2.children if c.name is not None]
    hijos_p3 = [c for c in nodo_p3.children if c.name is not None]

    for i, hijo_p3 in enumerate(hijos_p3):
        hijo_p2 = hijos_p2[i] if i < len(hijos_p2) else None
        if hijo_p2 and hijo_p2.name != hijo_p3.name:
            hijo_p2 = None 
        comparar_arboles(hijo_p2, hijo_p3)

def capturar_pantalla(page, ruta_relativa, ruta_salida, viewport=None, full_page=True, ajustar_body=False):
    if viewport:
        page.set_viewport_size(viewport)
    else:
        page.set_viewport_size({"width": 1280, "height": 800})
    
    # Navegación a través del servidor HTTP local en lugar de file://
    ruta_url = urllib.parse.quote(ruta_relativa.replace('\\', '/'))
    url_localhost = f"http://localhost:{PUERTO}/{ruta_url}"
    
    # networkidle asegura que Playwright espere a que finalicen las llamadas fetch de JSON/XML
    page.goto(url_localhost, wait_until='networkidle')
    
    if ajustar_body:
        elemento_cuerpo = page.locator("body")
        elemento_cuerpo.screenshot(path=ruta_salida)
    else:
        page.screenshot(path=ruta_salida, full_page=full_page)

def generar_mapas(archivo, page, directorio, sufijo_salida=''):
    """Genera mapas de etiquetas para un archivo HTML.
    
    Args:
        archivo: nombre del archivo HTML
        page: página de Playwright
        directorio: directorio desde el cual leer el archivo
        sufijo_salida: sufijo para añadir al nombre del archivo de salida
    """
    nombre_base = archivo.replace('.html', '')
    ruta_source = os.path.join(directorio, archivo)

    with open(ruta_source, 'r', encoding='utf-8') as f:
        soup_web = BeautifulSoup(f, 'html.parser')

    limpiar_y_preparar_arbol(soup_web)

    soup_normal = BeautifulSoup(str(soup_web), 'html.parser')
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
    
    nombre_salida = f"{nombre_base}{sufijo_salida}-boxmodel.png" if sufijo_salida else f"{nombre_base}-boxmodel.png"
    capturar_pantalla(page, ruta_tmp_normal, os.path.join(DIR_OUT_MAPAS, nombre_salida), ajustar_body=True)
    os.remove(ruta_tmp_normal)

def generar_capturas_reales_responsivas(archivo, page, directorio, sufijo_salida=''):
    """Genera capturas responsivas para un archivo HTML.
    
    Args:
        archivo: nombre del archivo HTML
        page: página de Playwright
        directorio: directorio desde el cual leer el archivo
        sufijo_salida: sufijo para añadir al nombre del archivo de salida
    """
    nombre_base = archivo.replace('.html', '')
    ruta_relativa = os.path.join(directorio, archivo)

    dispositivos = {
        'desktop': {'width': 1920, 'height': 1080},
        'tablet': {'width': 768, 'height': 1024},
        'mobile': {'width': 375, 'height': 812}
    }

    for disp, viewport in dispositivos.items():
        nombre_fichero = f"{nombre_base}{sufijo_salida}-{disp}.png" if sufijo_salida else f"{nombre_base}-{disp}.png"
        ruta_salida = os.path.join(DIR_OUT_CAPTURAS, nombre_fichero)
        capturar_pantalla(page, ruta_relativa, ruta_salida, viewport=viewport, ajustar_body=False, full_page=False)

if __name__ == '__main__':
    os.makedirs(DIR_OUT_MAPAS, exist_ok=True)
    os.makedirs(DIR_OUT_CAPTURAS, exist_ok=True)

    # Arranque del servidor HTTP en segundo plano
    print(f"Iniciando servidor local en el puerto {PUERTO}...")
    httpd = ServidorTCPReutilizable(("", PUERTO), ManejadorSilencioso)
    hilo_servidor = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo_servidor.start()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Generación de mapas antiguos (directorio DIR_P2)
        archivos_antiguos = [f for f in os.listdir(DIR_P2) if f.endswith('.html')]
        for archivo in archivos_antiguos:
            print(f"Procesando (antiguo) {archivo}...")
            generar_mapas(archivo, page, DIR_P2, sufijo_salida='')
            generar_capturas_reales_responsivas(archivo, page, DIR_P2, sufijo_salida='')

        # 2. Generación de mapas actuales (directorio DIR_P3)
        archivos_nuevos = [f for f in os.listdir(DIR_P3) if f.endswith('.html')]
        for archivo in archivos_nuevos:
            print(f"Procesando (nuevo) {archivo}...")
            generar_mapas(archivo, page, DIR_P3, sufijo_salida='-new')
            generar_capturas_reales_responsivas(archivo, page, DIR_P3, sufijo_salida='-new')

        browser.close()
        
    # Apagado del servidor
    httpd.shutdown()
    httpd.server_close()
    print("\n¡Proceso completado con éxito! Revisa la carpeta doc/")
