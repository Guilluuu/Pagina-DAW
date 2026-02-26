from bs4 import BeautifulSoup
from html2image import Html2Image
from PIL import Image, ImageChops
import os

def generar_diagrama_cajas(ruta_entrada, ruta_salida, max_depth):
    with open(ruta_entrada, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # 1. Limpieza y control de profundidad
    for tag in soup.find_all(True):
        profundidad = len(list(tag.parents))
        
        if profundidad > max_depth:
            tag.decompose()
        else:
            tag.attrs = {} 
            tag['data-etiqueta'] = tag.name 
            tag.name = 'div' 
            
            for text_node in tag.find_all(string=True, recursive=False):
                text_node.extract()
                
            # Fuerza el cierre explícito (<div> </div>) para evitar que Chromium anide las cajas
            if not tag.contents:
                tag.append(soup.new_string(' '))

    # 2. Inyección de reglas CSS
    estilos = soup.new_tag('style')
    estilos.string = """
        head, meta, title, link, script, style { display: none !important; }
        body { font-family: sans-serif; background: #f4f4f4; padding: 20px; }
        *[data-etiqueta] {
            border: 2px solid #2c3e50;
            padding: 10px; 
            margin: 10px;
            display: block;
            background: #ffffff;
            min-width: min-content; 
        }
        *[data-etiqueta]::before {
            content: attr(data-etiqueta);
            display: block; 
            font-weight: bold;
            color: #2980b9;
            margin-bottom: 5px;
        }
    """
    
    if not soup.head:
        soup.insert(0, soup.new_tag('head'))
    soup.head.append(estilos)

    # 3. Captura sobredimensionada
    hti = Html2Image()
    nombre_archivo = os.path.basename(ruta_salida)
    ruta_directorio = os.path.dirname(ruta_salida) or '.'
    
    hti.output_path = ruta_directorio
    hti.screenshot(html_str=str(soup), save_as=nombre_archivo, size=(1200, 5000))

    # 4. Recorte algorítmico dinámico del espacio sobrante
    ruta_completa = os.path.join(ruta_directorio, nombre_archivo)
    
    with Image.open(ruta_completa) as img:
        img_rgb = img.convert("RGB")
        
        # Muestreamos el color real del fondo (esquina inferior izquierda)
        color_fondo = img_rgb.getpixel((0, img_rgb.height - 1))
        
        # Comparamos la imagen contra un lienzo de su color de fondo real
        lienzo_fondo = Image.new("RGB", img_rgb.size, color_fondo)
        diferencia = ImageChops.difference(img_rgb, lienzo_fondo)
        caja_delimitadora = diferencia.getbbox() 
        
        if caja_delimitadora:
            # caja_delimitadora[3] es la altura máxima con contenido real
            altura_final = caja_delimitadora[3] + 20 # 20px de margen estético
            
            # Cortamos a la nueva altura calculada
            img_recortada = img.crop((0, 0, img.width, altura_final))
            img_recortada.save(ruta_completa)

if __name__ == '__main__':
    dir_input = 'input'
    dir_output = 'boxmodels'
    
    # Crea las carpetas automáticamente si no existen en tu sistema
    os.makedirs(dir_input, exist_ok=True)
    os.makedirs(dir_output, exist_ok=True)

    # Escanea el directorio input/ buscando ficheros HTML
    archivos_html = [f for f in os.listdir(dir_input) if f.endswith('.html')]
    
    if not archivos_html:
        print(f"No hay archivos .html en la carpeta '{dir_input}'.")
    else:
        for archivo in archivos_html:
            # Separa el nombre (ej. 'clinicas') de la extensión ('.html')
            nombre_base = os.path.splitext(archivo)[0]
            # Construye el nuevo nombre de salida
            nombre_salida = f"{nombre_base}-boxmodel.png"
            
            ruta_in = os.path.join(dir_input, archivo)
            ruta_out = os.path.join(dir_output, nombre_salida)
            
            print(f"Procesando: {archivo} -> {nombre_salida}")
            generar_diagrama_cajas(ruta_in, ruta_out, max_depth=4)
            
        print("Proceso completado exitosamente.")