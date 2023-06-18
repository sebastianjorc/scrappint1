import requests
from requests.exceptions import ChunkedEncodingError
import urllib.request
import random
import time

import re
import csv
import os
from bs4 import BeautifulSoup


dominio = 'https://chemicalguys.cl'
url = 'https://chemicalguys.cl/'#/collections/liquidos'
# Definir las cabeceras del archivo CSV
headers = ['Categoria', 'Subcategoria', 'Etiqueta', 'Marca', 'Título', 'URL Imagen', 'Precio', 'Descripción']
# Verificar si el archivo CSV existe
file_exists = os.path.isfile('chemicalguys.csv')
# Verificar si el archivo existe o está vacío
file_exists = os.path.isfile('chemicalguys.csv')
is_empty = os.stat('chemicalguys.csv').st_size == 0

# Abrir el archivo CSV en modo "agregar" o "escritura" al inicio del programa
with open('chemicalguys.csv', 'a+', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # Escribir las cabeceras solo si el archivo no existe o está vacío
    if not file_exists or is_empty:
        writer.writerow(headers)

def sleep_rnd():    
    tiempo_espera = random.uniform(3, 8)
    # Pausa durante el tiempo generado
    time.sleep(tiempo_espera)

def clean_filename(filename):
    # Reemplazar caracteres no válidos con guiones bajos
    cleaned_filename = re.sub(r'[\\/:*?"<>|]', '_', filename)

    # Eliminar todo después de "500x.jpg" en el nombre de archivo
    cleaned_filename = re.sub(r'\.jpg.*', '.jpg', cleaned_filename)
    return cleaned_filename

def hacer_solicitud(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except ChunkedEncodingError as e:
        print("Error de conexión durante la solicitud:", e)
        return None

def obtener_e(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    enlaces = soup.select('a')
    return enlaces

def guardar_datos_en_csv(enlaces, filename):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Texto', 'URL'])  # Escribir encabezados de columna

        for enlace in enlaces:
            texto = enlace.text
            url_enlace = enlace['href']
            writer.writerow([texto, url_enlace])
            sleep_rnd()

def obtener_enlaces_producto(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    enlaces_href = []
    enlaces = soup.find_all('a', class_='woocommerce-LoopProduct-link woocommerce-loop-product__link')
    for enlace in enlaces:
        href = enlace['href']
        enlaces_href.append(href)
        print('\n')
        print(href)
    return enlaces_href

def obtener_data_producto(html_content, carpeta_base):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Marca
    marca = 'chemical guys'

    # Titulo 
    h1_element = soup.find('h1', class_='product_title entry-title')
    if h1_element is not None:
        titulo = h1_element.get_text()        
        # Verificar si el título contiene un guion
        if "-" in titulo:
            # Dividir la cadena en dos partes usando el guion como separador
            partes = titulo.split("-", 1)
            # Obtener la segunda parte (a partir del primer carácter después del guion)
            titulo = partes[1].strip()
        # Carpeta específica para el producto
        nombre_carpeta_producto = clean_filename(titulo)
        # Ruta completa de la carpeta
        ruta_carpeta_producto = os.path.join(carpeta_base, nombre_carpeta_producto)
        # Crear la carpeta específica para el producto
        os.makedirs(ruta_carpeta_producto, exist_ok=True)
        print("\n"+titulo)

    # Precio
    price_element = soup.select_one('p.price bdi')
    if price_element:
        price = price_element.get_text(strip=True)
        precio_numerico = re.sub(r'[^0-9]', '', price)
        print("\nprecio: "+precio_numerico)
    else:
        print("No se encontró el elemento de precio")

    # Descripción
    # Verificar si se encontró el elemento con la clase 'product-form__text'
    product_form_element = soup.find(class_='woocommerce-product-details__short-description')    
    if product_form_element is not None:
        # Obtener todos los elementos <p> dentro del elemento 'product-form__text'
        parrafos = product_form_element.find_all('li')
        parrafos2 = product_form_element.find_all('p')
        descripcion = '\n'.join(parrafo.get_text() for parrafo in parrafos2)
        descripcion = descripcion + '\n'.join(parrafo.get_text() for parrafo in parrafos)
    else:
        descripcion = '' 
    descripcion2 = soup.find(class_='woocommerce-Tabs-panel woocommerce-Tabs-panel--description panel entry-content wc-tab')
    if descripcion2 is not None:
        parrafos = descripcion2.find_all('p')
        descripcion = descripcion + '\n'.join(parrafo.get_text() for parrafo in parrafos)
    print("\n"+descripcion)

    # Imagenes
    contenedor_enlaces_padre = soup.find('figure', class_='woocommerce-product-gallery__wrapper')
    enlaces_padre = contenedor_enlaces_padre.find_all('div', class_='woocommerce-product-gallery__image')
    enlaces_hijo = []
    contador = 1  # Inicializar el contador de imágenes

    for padre in enlaces_padre:
        image = padre.find('a')
        if image is not None:
            src = image['href']
            enlaces_hijo.append(src)
            # Obtener el nombre de archivo a partir del enlace y limpiarlo
            filename = os.path.basename(src)
            filename = clean_filename(filename)
            # Obtener el nuevo nombre de archivo con el formato "titulo-n.jpg"
            new_filename = f"{clean_filename(titulo)}-{contador}.jpg"
            # Ruta completa del archivo dentro de la carpeta
            filepath = os.path.join(ruta_carpeta_producto, new_filename)
            # Crear la carpeta específica para el producto si no existe
            os.makedirs(ruta_carpeta_producto, exist_ok=True)

            # Descargar la imagen y guardarla en un archivo local
            try:
                #print('\n\nFILENAME : '+filename)
                #print('RUTA_CARPETA : '+ruta_carpeta_producto)
                #print('SRC : '+src)
                #print('FILEPATH : '+filepath+'\n\n')
                # Crear la carpeta específica para el producto si no existe
                os.makedirs(ruta_carpeta_producto, exist_ok=True)
                urllib.request.urlretrieve(src, os.path.join(ruta_carpeta_producto, new_filename))
                #print("Imagen descargada:", filepath)
                contador += 1  # Incrementar el contador de imágenes
            except urllib.error.HTTPError as e:
                print("Error al descargar la imagen:", src)
                print("Código de error:", e.code)
            except urllib.error.URLError as e:
                print("Error de URL:", src)
                print("Mensaje de error:", e.reason)
    src_concatenados = ' '.join(enlaces_hijo)
    return marca, titulo, src_concatenados, precio_numerico, descripcion

def agregar_datos_a_csv(data):
    with open('chemicalguys.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(data)

def obtener_data_paginacion(url, plp, categoria, subcategoria, etiqueta):
    page = 1
    
    while True:
        # Agregar un tiempo de espera aleatorio para evitar ser bloqueado
        sleep_rnd()
        # Obtener el contenido HTML de la página actual
        html_content = hacer_solicitud(url)
        enlaces_producto = obtener_enlaces_producto(html_content)
        
        # Recorrer los enlaces de los productos en la página actual
        for enlace_producto in enlaces_producto:
            html_content = hacer_solicitud(enlace_producto)
            # Llamar a la función y asignar los valores retornados a variables individuales
            marca, titulo, src_concatenados, precio_numerico, descripcion = obtener_data_producto(html_content, plp) 
            data = [categoria, subcategoria, etiqueta, marca, titulo, src_concatenados, precio_numerico, descripcion]
            agregar_datos_a_csv(data)
        
        # Verificar si existe un enlace para la siguiente página
        html_content = hacer_solicitud(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        next_page_link = soup.find('a', class_='next page-numbers')
        if next_page_link is None:
            break  # No hay más páginas, salir del bucle
        
        # Obtener la URL de la siguiente página y actualizar el número de página
        url = next_page_link['href']
        page += 1


    print("Proceso de paginación completado")

    #enlaces = obtener_enlaces(html_content)
    #guardar_datos_en_csv(enlaces, 'datos_enlaces.csv')

def obtener_categorias(url):
    html_content = hacer_solicitud(url)
    soup = BeautifulSoup(html_content, 'html.parser')
    categorias_title = []
    subcategorias_title = []
    etiquetas_title = []
    
    ul_element = soup.find('ul', id="menu-1-756ec25")
    categorias = ul_element.find_all('li', recursive=False)
    for categoria in categorias:
        categoria_a = categoria.find('a')
        print(categoria_a)
        try: 
            categoria_title = categoria_a.get_text()
        except AttributeError:
            categoria_title = ''

        if (categoria_title == 'Nuevos!' or categoria_title == 'Ofertas!' or categoria_title == 'Kits' or categoria_title == 'Accesorios' or categoria_title == 'Exterior' or categoria_title == 'Interior'):
            # Acceder a los atributos o contenido del categoria <a>
            categorias_title.append(categoria_title)
            print("\n\nCATEGORIA: "+ categoria_title)
            # Crear la carpeta base si no existe
            nombre_carpeta_categoria = clean_filename(categoria_title)
            os.makedirs(nombre_carpeta_categoria, exist_ok=True)
            subcategorias = categoria.find_all('li')
            if subcategorias is not None and len(subcategorias) > 0:
                for subcategoria in subcategorias:
                    subcategoria_a = subcategoria.find('a')
                    subcategoria_title = subcategoria_a.get_text()
                    subcategorias_title.append(subcategoria_title)
                    print("\nSUBCATEGORIA: " + subcategoria_title)
                    url = subcategoria_a['href']
                    print(subcategoria_title+" : "+url)
                    # Ruta completa de la carpeta
                    nombre_carpeta_subcategoria = clean_filename(subcategoria_title) 
                    ruta_carpeta_subcategoria = os.path.join(nombre_carpeta_categoria, nombre_carpeta_subcategoria)
                    # Crear la carpeta específica para el producto
                    os.makedirs(ruta_carpeta_subcategoria, exist_ok=True)
                    obtener_data_paginacion(url,ruta_carpeta_subcategoria,categoria_title, subcategoria_title, '')
            else:
                url=categoria_a['href']
                print("ELSE : "+url)
                obtener_data_paginacion(url,nombre_carpeta_categoria,categoria_title, '', '')

    return categorias_title
    
categorias = obtener_categorias('https://chemicalguys.cl/')

#html_content = hacer_solicitud('https://chemicalguys.cl/producto/clay-kit-grey/')

#obtener_data_paginacion(url, 'carpeta', 'categoria','subcategoria','etiqueta')
#obtener_data_producto(html_content,'')
#obtener_data_paginacion(url,etiqueta)