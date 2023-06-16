import requests
from requests.exceptions import ChunkedEncodingError
import urllib.request
import random
import time

import re
import csv
import os
from bs4 import BeautifulSoup


dominio = 'https://www.adamspolishes.cl'
url = 'https://www.adamspolishes.cl'#/collections/liquidos'

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
    enlaces = soup.find_all('a', class_='product-item__aspect-ratio aspect-ratio')
    for enlace in enlaces:
        href = 'https://www.adamspolishes.cl'+enlace['href']
        enlaces_href.append(href)
        print('\n')
        print(href)
    return enlaces_href

def obtener_data_producto(html_content, carpeta_base):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Marca
    a_element = soup.find('h2', class_='product-meta__vendor heading heading--small').find('a')
    if a_element is not None:
        marca = a_element.get_text()
        #print(marca)

    # Titulo 
    h1_element = soup.find('h1', class_='product-meta__title heading h3')
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

    # Precio
    try:
        span_element = soup.find('span', class_='price price--large')
        precio = span_element.get_text()
        precio_numerico = re.sub(r'[^0-9]', '', precio)
    except AttributeError:
        span_element = soup.find('span', class_='price price--compare')
        precio = span_element.get_text()
        precio_numerico = re.sub(r'[^0-9]', '', precio)

    # Descripción
    # Verificar si se encontró el elemento con la clase 'product-form__text'
    product_form_element = soup.find(class_='product-form__text')
    if product_form_element is not None:
        # Obtener todos los elementos <p> dentro del elemento 'product-form__text'
        parrafos = product_form_element.find_all('p')
        descripcion = '\n'.join(parrafo.get_text() for parrafo in parrafos)
    else:
        descripcion = ''

    # Imagenes
    enlaces_padre = soup.find_all(class_='product__media-image-wrapper')
    enlaces_hijo = []
    contador = 1  # Inicializar el contador de imágenes
    for padre in enlaces_padre:
        img_element = padre.find('img')
        if img_element is not None:
            src = img_element['src']
            # Verificar si la URL comienza con '//'
            if src.startswith('//'):
                src = 'https:' + src
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
                print('\n\nFILENAME : '+filename)
                print('RUTA_CARPETA : '+ruta_carpeta_producto)
                print('SRC : '+src)
                print('FILEPATH : '+filepath+'\n\n')
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

def obtener_data_paginacion(url, plp):
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
            marca, titulo, src_concatenados, precio_numerico, descripcion = obtener_datos_producto(html_content, plp)
        
        # Verificar si existe un enlace para la siguiente página
        html_content = hacer_solicitud(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        next_page_link = soup.find('a', class_='pagination__nav-item', rel='next')
        if next_page_link is None:
            break  # No hay más páginas, salir del bucle
        
        # Obtener la URL de la siguiente página y actualizar el número de página
        url = dominio+next_page_link['href']
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
    categorias = soup.find_all('li', class_='header__linklist-item has-dropdown')

    for categoria in categorias:
        categoria_title = categoria['data-item-title']
        categorias_title.append(categoria_title)
        print("\n\nCATEGORIA: "+ categoria_title)
        # Crear la carpeta base si no existe
        nombre_carpeta_categoria = clean_filename(categoria_title) 
        os.makedirs(nombre_carpeta_categoria, exist_ok=True)
        #     
        div_subcategorias = categoria.find_all('div', class_='mega-menu__column')
        for div_subcategoria in div_subcategorias:
            subcategoria = div_subcategoria.find('a', class_='mega-menu__title heading heading--small')
            subcategoria_ul = div_subcategoria.find('ul', class_='linklist list--unstyled')

            subcategoria_title = subcategoria.get_text()
            subcategorias_title.append(subcategoria_title)
            print("\nSUBCATEGORIA: " + subcategoria_title)

            # Ruta completa de la carpeta
            nombre_carpeta_subcategoria = clean_filename(subcategoria_title) 
            ruta_carpeta_subcategoria = os.path.join(nombre_carpeta_categoria, nombre_carpeta_subcategoria)
            # Crear la carpeta específica para el producto
            os.makedirs(ruta_carpeta_subcategoria, exist_ok=True)
            #
            if subcategoria_ul:  # Verificamos si se encontró el elemento <ul>
                etiquetas = subcategoria_ul.find_all('a', class_='link--faded')
                for etiqueta in etiquetas:
                    etiqueta_title = etiqueta.get_text()
                    etiquetas_title.append(etiqueta_title)
                    
                    url = dominio+etiqueta['href']
                    print(etiqueta_title+" : "+url)
                    
                    # Ruta completa de la carpeta
                    nombre_carpeta_etiqueta = clean_filename(etiqueta_title) 
                    ruta_carpeta_etiqueta = os.path.join(ruta_carpeta_subcategoria, nombre_carpeta_etiqueta)
                    # Crear la carpeta específica para el producto
                    os.makedirs(ruta_carpeta_etiqueta, exist_ok=True)

                    obtener_data_paginacion(url,ruta_carpeta_etiqueta)
            else:
                url=dominio+subcategoria['href']
                print(" : "+url)
                obtener_data_paginacion(url,ruta_carpeta_subcategoria)

    return categorias_title
    
categorias = obtener_categorias(url)

#obtener_data_paginacion(url,etiqueta)