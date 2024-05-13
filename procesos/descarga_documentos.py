#0992429267001
#Asia2023**
import os
import sys
import time
import pyodbc
import requests
import speech_recognition as SR
import xml.etree.ElementTree as ET


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from datetime import datetime, timedelta
from pydub import AudioSegment
from funciones.validar_numero_autorizacion import validar_numero_autorizacion 
from funciones.conexion import obtener_conexion
from funciones.insertar_en_db import insertar_facturas
from funciones.insertar_en_db import insertar_retenciones

# Construye la cadena de conexión

conn_str = obtener_conexion()

try:
    # Establece la conexión
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Ejecuta una consulta de ejemplo
    cursor.execute("SELECT @@VERSION")
    print('asdasdasd')
    row = cursor.fetchone()
    
    # Imprime el resultado
    print("Versión de SQL Server:", row[0])

    # Cierra la conexión
    conn.close()


except pyodbc.Error as e:
    print("Error al conectar a la base de datos:", e)
    sys.exit()


def obtiene_facturas():
    download_dir = os.getcwd()

    llPruebaTodosDias = False
    
    download_dir = os.path.join(download_dir, "XML")

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    chrome_options = Options()

    chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,  # Configura el directorio de descarga
    "download.prompt_for_download": False,       # Desactiva la ventana de descarga
    "download.directory_upgrade": True,          # Gestiona la configuración del directorio
    "safebrowsing.enabled": True                 # Activar la navegación segura
    })
    
    current_directory = os.path.dirname(os.path.abspath(__file__))
    scrapy_directory = os.path.dirname(current_directory)    
    chromedriver_path = os.path.join(scrapy_directory, 'chromedriver.exe')
    
    # Configuración del driver
    s = Service(ChromeDriverManager().install())

    s = Service(chromedriver_path)

    driver = webdriver.Chrome(service=s, options=chrome_options)

    # Navegar a la página de login
    driver.get('https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-claves-angular&redirect_uri=https%3A%2F%2Fsrienlinea.sri.gob.ec%2Fsri-en-linea%2F%2Fcontribuyente%2Fperfil&state=be5eb439-0844-47a5-811e-0ae863e6fcd2&nonce=974dcae2-7a24-417d-b528-db77b124f4cf&response_mode=fragment&response_type=code&scope=openid')

    try:
        input_usuario = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.ID, 'usuario'))
        )
    except TimeoutException:
        print("El elemento 'usuario' no se hizo visible en la página dentro del tiempo de espera especificado.")
        
    try:
        input_contraseña = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.ID, 'password'))
        )
    except TimeoutException:
        print("El elemento 'usuario' no se hizo visible en la página dentro del tiempo de espera especificado.")


    input_usuario.send_keys('0992429267001')
    input_contraseña.send_keys('Asia2023**')

    # Opcional: Enviar el formulario
    input_contraseña.send_keys(Keys.ENTER)

    # Asegúrate de cerrar el navegador después de tu script



    elemento_menu = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.sri-menu-icon-menu-hamburguesa'))
    )
    elemento_menu.click()

    elemento_facturacion = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//span[@class="ui-menuitem-text" and text()="FACTURACIÓN ELECTRÓNICA"]'))
    )
    elemento_facturacion.click()



    elemento_comprobantes_recibidos = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//span[@class="ui-menuitem-text" and text()="Comprobantes electrónicos recibidos"]'))
    )
    elemento_comprobantes_recibidos.click()


    #------------------------------------------------------------------------------------------------------#
    #-------------------------------------Iniciando la generación de consulta------------------------------#
    #------------------------------------------------------------------------------------------------------#



    # Establecer manualmente la fecha actual para propósitos de prueba
    fecha_actual = datetime.now()

    # Obtener el día anterior
    if fecha_actual.day == 1:  # Si el día actual es el primero del mes, restamos un día
        if fecha_actual.month == 1:  # Si el mes actual es enero, restamos un año y seleccionamos diciembre
            dia_anterior = 31
            mes_anterior = 12
            anio_anterior = fecha_actual.year - 1
        elif fecha_actual.month in [2, 4, 6, 8, 9, 11]:  # Si el mes actual tiene 30 días
            dia_anterior = 31
            mes_anterior = fecha_actual.month - 1
            anio_anterior = fecha_actual.year
        elif fecha_actual.month == 3:  # Si el mes actual es marzo
            if fecha_actual.year % 4 == 0:  # Comprobamos si es un año bisiesto
                dia_anterior = 29
            else:
                dia_anterior = 28
            mes_anterior = 2
            anio_anterior = fecha_actual.year
        else:  # Si el mes actual es mayo, julio, octubre o diciembre
            dia_anterior = 30
            mes_anterior = fecha_actual.month - 1
            anio_anterior = fecha_actual.year
    else:
        dia_anterior = fecha_actual.day - 1
        mes_anterior = fecha_actual.month
        anio_anterior = fecha_actual.year
    if llPruebaTodosDias:
        dia_anterior = 0

    
    # Seleccionar el año, mes y día en los selectores de la página web
    driver.execute_script(f"document.getElementById('frmPrincipal:ano').value = '{anio_anterior}';")
    driver.execute_script(f"document.getElementById('frmPrincipal:mes').value = '{mes_anterior}';")
    driver.execute_script(f"document.getElementById('frmPrincipal:dia').value = '{dia_anterior}';")
    driver.execute_script("document.getElementById('frmPrincipal:cmbTipoComprobante').value = '1';")

    try:
        btn_consultar = driver.find_element(By.ID, "btnRecaptcha")

        btn_consultar.click()
    except ElementClickInterceptedException:
        print("No se pudo hacer clic en el botón 'Consultar'. Elemento no interactuable.")

    time.sleep(2)


    try:
        print("Ingresando a buscar el captcha")

        # Encontrar el iframe del reCAPTCHA
        
        iframe = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "iframe[title='El reCAPTCHA caduca dentro de dos minutos']"))
        )
        
        # Cambiar al contexto del iframe del reCAPTCHA
        driver.switch_to.frame(iframe)
        print("Se hizo switch")
        # Encontrar el contenedor que contiene la etiqueta footer
        footer_container = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.rc-footer"))
        )


        # Encontrar la etiqueta footer dentro del contenedor
        footer = footer_container.find_element(By.XPATH, ".//button[@id='recaptcha-verify-button']")
        
        rc_controls_container = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.rc-controls div.rc-buttons div.audio-button-holder"))
        )    
        rc_controls_container.click()

        # Encontrar el enlace que deseas hacer clic
        download_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.rc-audiochallenge-tdownload-link"))
        )

        audio_url = download_link.get_attribute('href')

        response = requests.get(audio_url)
        with open("audio.mp3", "wb") as f:
            f.write(response.content)    

            
        audio_file_name = "audio.mp3"
        current_directory = os.getcwd()
        audio_file_path = os.path.join(current_directory, audio_file_name)

        try:
            print("Intentando cargar el archivo MP3:", audio_file_path)
            audio = AudioSegment.from_mp3(audio_file_path)
        except Exception as e:
            print("Error al cargar el archivo MP3:", e)
            exit(1)

        wav_file_path = os.path.join(current_directory, "audio.wav")

        try:
            print("Exportando a WAV...")
            audio.export(wav_file_path, format="wav")
        except Exception as e:
            print("Error al exportar a WAV:", e)
            exit(1)

        recognizer = SR.Recognizer()
        try:
            with SR.AudioFile(wav_file_path) as source:
                #Escuchando el audio...
                audio_data = recognizer.listen(source)
                #Reconociendo el audio...
                text = recognizer.recognize_google(audio_data, language='es-ES')
                #Texto reconocido
                input_audio_response = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.ID, "audio-response"))
                )

                driver.execute_script("arguments[0].value = arguments[1];", input_audio_response, text)

                input_audio_response.clear()  # Limpiar cualquier texto existente
                input_audio_response.send_keys(text)

                # Localizar el botón de verificación por su ID
                verify_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "recaptcha-verify-button"))
                )

                # Hacer clic en el botón de verificación
                verify_button.click()            


        except SR.UnknownValueError:
            print('Google no pudo entender el audio')
        except SR.RequestError as e:
            print(f'No se pudo solicitar resultados; {e}')
        except Exception as e:
            print('Error al procesar el audio:', e)


    except ElementClickInterceptedException:
        print("No se pudo hacer clic en el botón 'Consultar'. Elemento no interactuable.")

    except TimeoutException:
        print("No existe el captcha.")    

    driver.switch_to.default_content()


    print('Comienza el recorrido de tabla')

    try:
        tabla = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "frmPrincipal:tablaCompRecibidos"))
        )
        # Continuar con el procesamiento de la tabla
    except TimeoutException:    
        print(f"No existe información para el día {dia_anterior:02d}-{mes_anterior:02d}-{anio_anterior}")
        sys.exit()

    # Ahora que la tabla es visible, encuentra todas las filas dentro de ella
    filas = WebDriverWait(tabla, 20).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
    )

    root_dir = os.getcwd()

    # Ruta del directorio "XML"
    xml_dir = os.path.join(root_dir, "XML")

    # Verifica si la carpeta "XML" existe
    if os.path.exists(xml_dir) and os.path.isdir(xml_dir):
        # Si existe, borra todos los archivos dentro de ella
        for file in os.listdir(xml_dir):
            file_path = os.path.join(xml_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"No se pudo borrar el archivo {file}: {e}")
    else:
        print("La carpeta 'XML' no existe en el directorio actual.")

    while True:
        
        # Ejecutar JavaScript para desplazarte hacia arriba en la página
        print('Sube la pagina')
        driver.execute_script("window.scrollTo(0, 0);")


        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            if len(celdas) >= 10:
                codigo_unico = celdas[3].text  # Lee el código único de la columna 4
                celda_descarga = celdas[9]
                enlace = celda_descarga.find_element(By.TAG_NAME, "a")
                enlace.click()
                
                descargado = False
                while not descargado:
                    for filename in os.listdir(download_dir):
                        if filename.startswith("Factura") and filename.endswith(".xml"):  # Ajusta según cómo se llamen los archivos
                            os.rename(os.path.join(download_dir, filename), os.path.join(download_dir, f"{codigo_unico}.xml"))
                            descargado = True
                            break

        # Verificar si el botón siguiente está habilitado para dar clic
        pie_pagina = driver.find_element(By.TAG_NAME, 'tfoot')

        boton_siguiente = pie_pagina.find_element(By.CLASS_NAME, 'ui-paginator-next')

        if "ui-state-disabled" not in boton_siguiente.get_attribute("class"):
            # Si el botón está habilitado, hacer clic en él y esperar un momento para que la página cargue
            boton_siguiente.click()
            time.sleep(5)  # Espera unos segundos para que la página cargue completamente
            # Actualizar la lista de filas después de la navegación
            filas = driver.find_elements(By.TAG_NAME, "tr")
        else:
            print("El botón siguiente está deshabilitado y no se puede dar clic")
            break  # Salir del bucle while si el botón está deshabilitado

    print('Termino de descargar')
    print('Comenzando a leer registros y guardar en la base de datos')

    insertar_facturas()

def obtiene_retenciones():
    download_dir = os.getcwd()

    llPruebaTodosDias = False

    download_dir = os.path.join(download_dir, "XML")

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    chrome_options = Options()

    chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,  # Configura el directorio de descarga
    "download.prompt_for_download": False,       # Desactiva la ventana de descarga
    "download.directory_upgrade": True,          # Gestiona la configuración del directorio
    "safebrowsing.enabled": True                 # Activar la navegación segura
    })

    # Configuración del driver
    s = Service(ChromeDriverManager().install())
    s = Service(r'C:\Users\DUI\Desktop\scrapy\chromedriver.exe')

    driver = webdriver.Chrome(service=s, options=chrome_options)

    # Navegar a la página de login
    driver.get('https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-claves-angular&redirect_uri=https%3A%2F%2Fsrienlinea.sri.gob.ec%2Fsri-en-linea%2F%2Fcontribuyente%2Fperfil&state=be5eb439-0844-47a5-811e-0ae863e6fcd2&nonce=974dcae2-7a24-417d-b528-db77b124f4cf&response_mode=fragment&response_type=code&scope=openid')

    try:
        input_usuario = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.ID, 'usuario'))
        )
    except TimeoutException:
        print("El elemento 'usuario' no se hizo visible en la página dentro del tiempo de espera especificado.")
        
    try:
        input_contraseña = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.ID, 'password'))
        )
    except TimeoutException:
        print("El elemento 'usuario' no se hizo visible en la página dentro del tiempo de espera especificado.")


    input_usuario.send_keys('0992429267001')
    input_contraseña.send_keys('Asia2023**')

    # Opcional: Enviar el formulario
    input_contraseña.send_keys(Keys.ENTER)

    # Asegúrate de cerrar el navegador después de tu script



    elemento_menu = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.sri-menu-icon-menu-hamburguesa'))
    )
    elemento_menu.click()

    elemento_facturacion = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//span[@class="ui-menuitem-text" and text()="FACTURACIÓN ELECTRÓNICA"]'))
    )
    elemento_facturacion.click()



    elemento_comprobantes_recibidos = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//span[@class="ui-menuitem-text" and text()="Comprobantes electrónicos recibidos"]'))
    )
    elemento_comprobantes_recibidos.click()


    #------------------------------------------------------------------------------------------------------#
    #-------------------------------------Iniciando la generación de consulta------------------------------#
    #------------------------------------------------------------------------------------------------------#



    # Establecer manualmente la fecha actual para propósitos de prueba
    fecha_actual = datetime.now()

    # Obtener el día anterior
    if fecha_actual.day == 1:  # Si el día actual es el primero del mes, restamos un día
        if fecha_actual.month == 1:  # Si el mes actual es enero, restamos un año y seleccionamos diciembre
            dia_anterior = 31
            mes_anterior = 12
            anio_anterior = fecha_actual.year - 1
        elif fecha_actual.month in [2, 4, 6, 8, 9, 11]:  # Si el mes actual tiene 30 días
            dia_anterior = 31
            mes_anterior = fecha_actual.month - 1
            anio_anterior = fecha_actual.year
        elif fecha_actual.month == 3:  # Si el mes actual es marzo
            if fecha_actual.year % 4 == 0:  # Comprobamos si es un año bisiesto
                dia_anterior = 29
            else:
                dia_anterior = 28
            mes_anterior = 2
            anio_anterior = fecha_actual.year
        else:  # Si el mes actual es mayo, julio, octubre o diciembre
            dia_anterior = 30
            mes_anterior = fecha_actual.month - 1
            anio_anterior = fecha_actual.year
    else:
        dia_anterior = fecha_actual.day - 1
        mes_anterior = fecha_actual.month
        anio_anterior = fecha_actual.year
    
    if llPruebaTodosDias: 
        dia_anterior = 0
    
    # Seleccionar el año, mes y día en los selectores de la página web
    driver.execute_script(f"document.getElementById('frmPrincipal:ano').value = '{anio_anterior}';")
    driver.execute_script(f"document.getElementById('frmPrincipal:mes').value = '{mes_anterior}';")
    driver.execute_script(f"document.getElementById('frmPrincipal:dia').value = '{dia_anterior}';")
    driver.execute_script("document.getElementById('frmPrincipal:cmbTipoComprobante').value = '6';")

    try:
        btn_consultar = driver.find_element(By.ID, "btnRecaptcha")

        btn_consultar.click()
    except ElementClickInterceptedException:
        print("No se pudo hacer clic en el botón 'Consultar'. Elemento no interactuable.")

    time.sleep(2)


    try:
        print("Ingresando a buscar el captcha")

        # Encontrar el iframe del reCAPTCHA
        
        iframe = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "iframe[title='El reCAPTCHA caduca dentro de dos minutos']"))
        )
        
        # Cambiar al contexto del iframe del reCAPTCHA
        driver.switch_to.frame(iframe)
        print("Se hizo switch")
        # Encontrar el contenedor que contiene la etiqueta footer
        footer_container = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.rc-footer"))
        )


        # Encontrar la etiqueta footer dentro del contenedor
        footer = footer_container.find_element(By.XPATH, ".//button[@id='recaptcha-verify-button']")
        
        rc_controls_container = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.rc-controls div.rc-buttons div.audio-button-holder"))
        )    
        rc_controls_container.click()

        # Encontrar el enlace que deseas hacer clic
        download_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.rc-audiochallenge-tdownload-link"))
        )

        audio_url = download_link.get_attribute('href')

        response = requests.get(audio_url)
        with open("audio.mp3", "wb") as f:
            f.write(response.content)    

            
        audio_file_name = "audio.mp3"
        current_directory = os.getcwd()
        audio_file_path = os.path.join(current_directory, audio_file_name)

        try:
            print("Intentando cargar el archivo MP3:", audio_file_path)
            audio = AudioSegment.from_mp3(audio_file_path)
        except Exception as e:
            print("Error al cargar el archivo MP3:", e)
            exit(1)

        wav_file_path = os.path.join(current_directory, "audio.wav")

        try:
            print("Exportando a WAV...")
            audio.export(wav_file_path, format="wav")
        except Exception as e:
            print("Error al exportar a WAV:", e)
            exit(1)

        recognizer = SR.Recognizer()
        try:
            with SR.AudioFile(wav_file_path) as source:
                #Escuchando el audio...
                audio_data = recognizer.listen(source)
                #Reconociendo el audio...
                text = recognizer.recognize_google(audio_data, language='es-ES')
                #Texto reconocido
                input_audio_response = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.ID, "audio-response"))
                )

                driver.execute_script("arguments[0].value = arguments[1];", input_audio_response, text)

                input_audio_response.clear()  # Limpiar cualquier texto existente
                input_audio_response.send_keys(text)

                # Localizar el botón de verificación por su ID
                verify_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "recaptcha-verify-button"))
                )

                # Hacer clic en el botón de verificación
                verify_button.click()            


        except SR.UnknownValueError:
            print('Google no pudo entender el audio')
        except SR.RequestError as e:
            print(f'No se pudo solicitar resultados; {e}')
        except Exception as e:
            print('Error al procesar el audio:', e)


    except ElementClickInterceptedException:
        print("No se pudo hacer clic en el botón 'Consultar'. Elemento no interactuable.")

    except TimeoutException:
        print("No existe el captcha.")    

    driver.switch_to.default_content()


    print('Comienza el recorrido de tabla')

    try:
        tabla = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "frmPrincipal:tablaCompRecibidos"))
        )
        # Continuar con el procesamiento de la tabla
    except TimeoutException:    
        print(f"No existe información para el día {dia_anterior:02d}-{mes_anterior:02d}-{anio_anterior}")
        sys.exit()

    # Ahora que la tabla es visible, encuentra todas las filas dentro de ella
    filas = WebDriverWait(tabla, 20).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
    )

    root_dir = os.getcwd()

    # Ruta del directorio "XML"
    xml_dir = os.path.join(root_dir, "XML")

    # Verifica si la carpeta "XML" existe
    if os.path.exists(xml_dir) and os.path.isdir(xml_dir):
        # Si existe, borra todos los archivos dentro de ella
        for file in os.listdir(xml_dir):
            file_path = os.path.join(xml_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"No se pudo borrar el archivo {file}: {e}")
    else:
        print("La carpeta 'XML' no existe en el directorio actual.")

    while True:
        
        # Ejecutar JavaScript para desplazarte hacia arriba en la página
        print('Sube la pagina')
        driver.execute_script("window.scrollTo(0, 0);")


        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            if len(celdas) >= 10:
                codigo_unico = celdas[3].text  # Lee el código único de la columna 4
                celda_descarga = celdas[9]
                enlace = celda_descarga.find_element(By.TAG_NAME, "a")
                enlace.click()
                
                descargado = False
                while not descargado:
                    for filename in os.listdir(download_dir):
                        if filename.startswith("Comprobante de Retención") and filename.endswith(".xml"):  # Ajusta según cómo se llamen los archivos
                            os.rename(os.path.join(download_dir, filename), os.path.join(download_dir, f"{codigo_unico}.xml"))
                            descargado = True
                            break

        # Verificar si el botón siguiente está habilitado para dar clic
        pie_pagina = driver.find_element(By.TAG_NAME, 'tfoot')

        boton_siguiente = pie_pagina.find_element(By.CLASS_NAME, 'ui-paginator-next')

        if "ui-state-disabled" not in boton_siguiente.get_attribute("class"):
            # Si el botón está habilitado, hacer clic en él y esperar un momento para que la página cargue
            boton_siguiente.click()
            time.sleep(5)  # Espera unos segundos para que la página cargue completamente
            # Actualizar la lista de filas después de la navegación
            filas = driver.find_elements(By.TAG_NAME, "tr")
        else:
            print("El botón siguiente está deshabilitado y no se puede dar clic")
            break  # Salir del bucle while si el botón está deshabilitado

    print('Termino de descargar')
    print('Comenzando a leer registros y guardar en la base de datos')

    insertar_retenciones()    