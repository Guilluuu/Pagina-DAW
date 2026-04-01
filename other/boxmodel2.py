from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
import os

ETIQUETAS_BLOQUE = {
    'main', 'header', 'footer', 'nav', 'aside',
    'section', 'article', 'div', 'form', 'table', 'thead', 'tbody',
    'tfoot', 'tr', 'th', 'td', 'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'figure', 'figcaption', 'details', 'summary', 'dialog', 'address',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'pre',
    'fieldset', 'legend', 'caption', 'colgroup', 'col',
}

ETIQUETAS_ELIMINAR = {
    'head', 'script', 'style', 'meta', 'link', 'noscript', 'template',
    'iframe', 'object', 'embed', 'svg', 'canvas', 'video', 'audio',
}

ESTILOS_BASE = """
    body {
        font-family: monospace;
        background: #ffffff;
        padding: 24px;
        font-size: 12px;
    }
    div.box {
        border: 1px solid #888888;
        padding: 4px;
        margin: 2px;
        min-height: 1em;
    }
    .box-label {
        display: block; 
        margin-bottom: 4px;
        white-space: nowrap;
    }
    .tag-name {
        font-weight: bold;
        color: #444444;
    }
"""

def limpiar_arbol(soup):
    for tag in soup.find_all(ETIQUETAS_ELIMINAR):
        tag.decompose()
    
    for tag in reversed(soup.find_all(True)):
        if tag.name == '[document]':
            continue
        if tag.name not in ETIQUETAS_BLOQUE:
            if tag.get('class'):
                padre = tag.parent
                if padre and padre.name != '[document]':
                    clases_padre = padre.get('class', [])
                    if isinstance(clases_padre, str):
                        clases_padre = clases_padre.split()
                    clases_padre.extend(tag.get('class', []))
                    padre['class'] = list(set(clases_padre))
            tag.unwrap()

def limitar_profundidad(soup, max_depth):
    for tag in reversed(soup.find_all(True)):
        if len(list(tag.parents)) > max_depth:
            tag.decompose()

def capturar_y_recortar(soup, ruta_salida):
    nombre_archivo = os.path.basename(ruta_salida)
    ruta_directorio = os.path.dirname(ruta_salida) or '.'
    ruta_completa = os.path.join(ruta_directorio, nombre_archivo)

    with sync_playwright() as p:
        browser = p.firefox.launch()
        page = browser.new_page(viewport={'width': 1200, 'height': 5000})
        page.set_content(str(soup), wait_until='load')
        page.screenshot(path=ruta_completa, full_page=True)
        browser.close()

    with Image.open(ruta_completa) as img:
        img_rgb = img.convert("RGB")
        color_fondo = img_rgb.getpixel((0, img_rgb.height - 1))
        lienzo_fondo = Image.new("RGB", img_rgb.size, color_fondo)
        diferencia = ImageChops.difference(img_rgb, lienzo_fondo)
        caja_delimitadora = diferencia.getbbox()

        if caja_delimitadora:
            altura_final = caja_delimitadora[3] + 20
            img_recortada = img.crop((0, 0, img.width, altura_final))
            img_recortada.save(ruta_completa)

def generar_diagrama_cajas(ruta_entrada, ruta_salida, max_depth):
    with open(ruta_entrada, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    limpiar_arbol(soup)
    limitar_profundidad(soup, max_depth)

    for tag in soup.find_all(True):
        for text_node in tag.find_all(string=True, recursive=False):
            text_node.extract()

        nombre_original = tag.name.lower()
        
        tag.attrs = {}
        tag.name = 'div'
        tag['class'] = ['box']
        
        label_div = soup.new_tag('div')
        label_div['class'] = ['box-label']
        
        span_titulo = soup.new_tag('span')
        span_titulo['class'] = ['tag-name']
        span_titulo.string = nombre_original
        label_div.append(span_titulo)
        
        tag.insert(0, label_div)

    estilos = soup.new_tag('style')
    estilos.string = ESTILOS_BASE
    if not soup.head:
        soup.insert(0, soup.new_tag('head'))
    soup.head.append(estilos)

    capturar_y_recortar(soup, ruta_salida)

def generar_diagrama_cajas_nuevo(ruta_nuevo, ruta_salida, max_depth):
    """Genera diagrama de cajas para el HTML nuevo sin resaltar cambios en rojo."""
    with open(ruta_nuevo, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    limpiar_arbol(soup)
    limitar_profundidad(soup, max_depth)

    for tag in soup.find_all(True):
        # Extraer atributos id y class para mostrarlos (opcional)
        todas_las_clases = tag.get('class', [])
        el_id = tag.get('id')

        texto_etiqueta = tag.name.lower()
        
        partes_atributos = []
        if el_id:
            partes_atributos.append(f'id="{el_id}"')
        if todas_las_clases:
            # Normalizar las clases a una cadena ordenada
            if isinstance(todas_las_clases, str):
                clases_ordenadas = sorted(todas_las_clases.split())
            else:
                clases_ordenadas = sorted(todas_las_clases)
            partes_atributos.append(f'class="{" ".join(clases_ordenadas)}"')
        
        texto_atributos = " ".join(partes_atributos)

        # Eliminar texto directo (se perderá en la visualización)
        for text_node in tag.find_all(string=True, recursive=False):
            text_node.extract()

        # Transformar el tag a un div con la caja
        tag.attrs = {}
        tag.name = 'div'
        tag['class'] = ['box']
        
        label_div = soup.new_tag('div')
        label_div['class'] = ['box-label']
        
        span_titulo = soup.new_tag('span')
        span_titulo['class'] = ['tag-name']
        span_titulo.string = texto_etiqueta
        label_div.append(span_titulo)
        
        if texto_atributos:
            span_attr = soup.new_tag('span')
            span_attr['class'] = ['attr-tag']  # Sin estilo rojo porque no se incluye ESTILOS_NUEVO
            span_attr.string = " " + texto_atributos
            label_div.append(span_attr)
            
        tag.insert(0, label_div)

    estilos = soup.new_tag('style')
    estilos.string = ESTILOS_BASE  # Sin ESTILOS_NUEVO, por lo que no hay rojo

    if not soup.head:
        soup.insert(0, soup.new_tag('head'))
    soup.head.append(estilos)

    capturar_y_recortar(soup, ruta_salida)


if __name__ == '__main__':
    dir_input = 'input'
    dir_output = 'boxmodels'

    os.makedirs(dir_input, exist_ok=True)
    os.makedirs(dir_output, exist_ok=True)

    todos_los_archivos = os.listdir(dir_input)
    archivos_base = [f for f in todos_los_archivos if f.endswith('.html') and not f.endswith('-nuevo.html')]

    if not archivos_base:
        print(f"No hay archivos base .html en la carpeta '{dir_input}'.")
    else:
        for archivo in archivos_base:
            nombre_base = archivo.replace('.html', '')
            archivo_nuevo = f"{nombre_base}-nuevo.html"

            ruta_in = os.path.join(dir_input, archivo)
            ruta_out = os.path.join(dir_output, f"{nombre_base}-boxmodel.png")

            print(f"Procesando original: {archivo} -> {nombre_base}-boxmodel.png")
            generar_diagrama_cajas(ruta_in, ruta_out, max_depth=6)

            ruta_in_nuevo = os.path.join(dir_input, archivo_nuevo)
            if archivo_nuevo in todos_los_archivos:
                ruta_out_nuevo = os.path.join(dir_output, f"{nombre_base}-nuevo-boxmodel.png")
                print(f"Procesando nuevo:    {archivo_nuevo} -> {nombre_base}-nuevo-boxmodel.png")
                generar_diagrama_cajas_nuevo(ruta_in_nuevo, ruta_out_nuevo, max_depth=6)
            
            print("-" * 40)

        print("Proceso completado exitosamente.")