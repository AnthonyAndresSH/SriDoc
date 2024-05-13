import os
import time
import pyodbc
import xml.etree.ElementTree as ET
import sys

from funciones.validar_numero_autorizacion import validar_numero_autorizacion 
from funciones.validar_numero_autorizacion import validar_numero_autorizacion_ret
from funciones.conexion import obtener_conexion
from datetime import datetime, timedelta

def insertar_facturas():
    conn_str = obtener_conexion()
    errores_insercion = []

    try:
        # Establece la conexión
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Ejecuta una consulta de ejemplo
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()

        # Cierra la conexión
        conn.close()

    except pyodbc.Error as e:
        print("Error al conectar a la base de datos:", e)
        sys.exit()
    # Obtiene la ruta donde se ejcuta el programa
    current_directory = os.getcwd()
    # Une la ruta con la carpeta XML
    directory = os.path.join(current_directory, "XML")
    # Obtiene los archivos del directorio
    files = os.listdir(directory)

    #Recorre  lista de archivos cada archivo
    for filename in files:
        #Si el archivo termina en .xml ingresa
        if filename.endswith(".xml") and filename[8:10] == "01":
            #Obtiene la ruta del archivo del directorio 
            filepath = os.path.join(directory, filename)
            
            # Parsear el archivo XML
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Extraer información del Grupo Cabecera
            autorizacion = root.find(".//numeroAutorizacion").text

            llExisteAutorizacion = validar_numero_autorizacion(autorizacion,conn_str)
            if llExisteAutorizacion:
                print("Saltanto al siguiente registro")
                continue

            # Obtener el contenido del CDATA
            cdata_content = root.find(".//comprobante").text

            # Parsear el contenido del CDATA como un nuevo árbol XML
            comprobante_root = ET.fromstring(cdata_content)
            
            # Ahora puedes buscar dentro del árbol 'comprobante_root'
            info_tributaria = comprobante_root.find(".//infoTributaria")
            info_factura = comprobante_root.find(".//infoFactura")
            
            tipo = 'FV'  # Valor quemado por defecto
            # Extraer información del Grupo Movimientos
            
            documento = "-".join([info_tributaria.find(".//estab").text, info_tributaria.find(".//ptoEmi").text, info_tributaria.find(".//secuencial").text])
            ruc = info_tributaria.find(".//ruc").text
            razon_social = info_tributaria.find(".//razonSocial").text
            fecha_emision = info_factura.find(".//fechaEmision").text
            fecha_emision = datetime.strptime(fecha_emision, "%d/%m/%Y")
            fecha_emision = fecha_emision.strftime("%Y%m%d")

            fecha_autorizacion = root.find(".//fechaAutorizacion").text
            fecha_autorizacion = datetime.fromisoformat(fecha_autorizacion)
            fecha_autorizacion = fecha_autorizacion.strftime("%Y-%m-%dT%H:%M:%S")

            clave_acceso = info_tributaria.find(".//claveAcceso").text
            importe_total = info_factura.find(".//totalSinImpuestos").text
            tipo_emision = 'NORMAL'  # Valor quemado por defecto
            numrel = 'test'  # Valor quemado por defecto              
            
            # Insertar datos en la tabla SRI_CABXMLRECIBIDO
            try:
                # Establece la conexión
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                
                # Insertar datos en la tabla SRI_CABXMLRECIBIDO
                insert_query = """
                    INSERT INTO SRI_CABXMLRECIBIDO (
                        AUTORIZACION, 
                        TIPO, 
                        DOCUMENTO, 
                        RUC, 
                        RAZON_SOCIAL, 
                        FECHA_EMISION, 
                        FECHA_AUTORIZACION, 
                        TIPO_EMISION, 
                        NUMREL, 
                        CLAVE_ACCESO, 
                        IMPORTE_TOTAL
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                # Datos para la inserción
                data = (
                    autorizacion, 
                    tipo, 
                    documento, 
                    ruc, 
                    razon_social, 
                    fecha_emision, 
                    fecha_autorizacion, 
                    tipo_emision, 
                    numrel, 
                    clave_acceso, 
                    importe_total
                )

                # Ejecutar la consulta de inserción
                cursor.execute(insert_query, data)

                # Confirmar la transacción
                conn.commit()
                # Cerrar la conexión
                conn.close()

            except pyodbc.Error as e:
                # Imprimir mensaje de error en caso de fallar la inserción
                print("Error al insertar datos en la tabla SRI_CABXMLRECIBIDO:", e)
                errores_insercion.append(autorizacion)  # Agregar número de autorización con error a la lista de errores

                    
            # Extraer información del Grupo Movimientos
            movimientos = comprobante_root.findall(".//detalles/detalle")
            for movimiento in movimientos:
                codigo = movimiento.find(".//codigoPrincipal").text
                nombre = movimiento.find(".//descripcion").text
                cantidad = movimiento.find(".//cantidad").text
                costo = movimiento.find(".//precioUnitario").text
                descuento = movimiento.find(".//descuento").text
                precio_tot = movimiento.find(".//precioTotalSinImpuesto").text
                impuesto_element = movimiento.find(".//impuestos/impuesto")
                tipo_iva = impuesto_element.find(".//codigo").text
                tipo_impuesto = impuesto_element.find(".//codigoPorcentaje").text
                val_impuesto = impuesto_element.find(".//valor").text
                tipo_ice = ''  # Valor quemado por defecto
                val_ice = '0.00'  # Valor quemado por defecto
                
                # Insertar datos en la tabla SRI_movXMLRECIBIDO
                try:
                    # Establecer la conexión
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()
                    
                    # Insertar datos en la tabla SRI_movXMLRECIBIDO
                    insert_query = """
                        INSERT INTO SRI_movXMLRECIBIDO (
                            AUTORIZACION, 
                            CODIGO, 
                            NOMBRE, 
                            CANTIDAD, 
                            COSTO, 
                            DESCUENTO, 
                            PRECIOTOT, 
                            TIPOIVA, 
                            TIPOIMPUESTO, 
                            VALIMPUESTO, 
                            TIPOICE, 
                            VALICE
                        ) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """

                    # Datos para la inserción
                    data = (
                        autorizacion, 
                        codigo, 
                        nombre, 
                        cantidad, 
                        costo, 
                        descuento, 
                        precio_tot, 
                        tipo_iva, 
                        tipo_impuesto, 
                        val_impuesto, 
                        tipo_ice, 
                        val_ice
                    )

                    # Ejecutar la consulta de inserción
                    cursor.execute(insert_query, data)

                    # Confirmar la transacción
                    conn.commit()
                    # Cerrar la conexión
                    conn.close()

                except pyodbc.Error as e:
                    print("Error al insertar datos en la tabla SRI_movXMLRECIBIDO:", e)
                    errores_insercion.append(autorizacion) 
    # Imprimir los números de autorización con problemas de inserción
    if errores_insercion:
        print("Existieron problemas en la inserción. Verifique los siguientes archivos:")
        for autorizacion in errores_insercion:
            print(autorizacion)

def insertar_retenciones():
    conn_str = obtener_conexion()
    errores_insercion = []

    try:
        # Establece la conexión
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Ejecuta una consulta de ejemplo
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        
        # Imprime el resultado
        print("Versión de SQL Server:", row[0])

        # Cierra la conexión
        conn.close()

    except pyodbc.Error as e:
        print("Error al conectar a la base de datos:", e)
        sys.exit()
    # Obtiene la ruta donde se ejcuta el programa
    current_directory = os.getcwd()
    # Une la ruta con la carpeta XML
    directory = os.path.join(current_directory, "XML")
    # Obtiene los archivos del directorio
    files = os.listdir(directory)

    #Recorre  lista de archivos cada archivo
    for filename in files:
        #Si el archivo termina en .xml ingresa
        if filename.endswith(".xml") and filename[8:10] == "07":
            #Obtiene la ruta del archivo del directorio 
            filepath = os.path.join(directory, filename)
            
            # Parsear el archivo XML
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Extraer información del Grupo Cabecera
            autorizacion = root.find(".//numeroAutorizacion").text

            llExisteAutorizacion = validar_numero_autorizacion_ret(autorizacion,conn_str)
            if llExisteAutorizacion:
                print("Saltanto al siguiente registro")
                continue

            # Obtener el contenido del CDATA
            cdata_content = root.find(".//comprobante").text

            # Parsear el contenido del CDATA como un nuevo árbol XML
            comprobante_root = ET.fromstring(cdata_content)
            
            # Ahora puedes buscar dentro del árbol 'comprobante_root'
            info_tributaria = comprobante_root.find(".//infoTributaria")
            info_retencion = comprobante_root.find(".//infoCompRetencion")
            tipo = 'RT'  # Valor quemado por defecto
            # Extraer información del Grupo Movimientos
            
            documento = "-".join([info_tributaria.find(".//estab").text, info_tributaria.find(".//ptoEmi").text, info_tributaria.find(".//secuencial").text])
            ruc = info_tributaria.find(".//ruc").text
            razon_social = info_tributaria.find(".//razonSocial").text
            
            fecha_emision = info_retencion.find(".//fechaEmision").text
            fecha_emision = datetime.strptime(fecha_emision, "%d/%m/%Y")
            fecha_emision = fecha_emision.strftime("%Y%m%d")

            fecha_autorizacion = root.find(".//fechaAutorizacion").text
            fecha_autorizacion = datetime.fromisoformat(fecha_autorizacion)
            fecha_autorizacion = fecha_autorizacion.strftime("%Y-%m-%dT%H:%M:%S")

            clave_acceso = info_tributaria.find(".//claveAcceso").text
            importe_total = 0.00
            tipo_emision = '1'  # Valor quemado por defecto
            numrel = 'test'  # Valor quemado por defecto              
            
            # Insertar datos en la tabla SRI_CABXMLRECIBIDO
            try:
                # Establece la conexión
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                
                # Insertar datos en la tabla SRI_CABXMLRECIBIDO
                insert_query = """
                    INSERT INTO SRI_CABRETXMLRECIBIDO (
                        AUTORIZACION, 
                        TIPO, 
                        DOCUMENTO, 
                        RUC, 
                        RAZON_SOCIAL, 
                        FECHA_EMISION, 
                        FECHA_AUTORIZACION, 
                        TIPO_EMISION, 
                        NUMREL, 
                        CLAVE_ACCESO, 
                        IMPORTE_TOTAL
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                # Datos para la inserción
                data = (
                    autorizacion, 
                    tipo, 
                    documento, 
                    ruc, 
                    razon_social, 
                    fecha_emision, 
                    fecha_autorizacion, 
                    tipo_emision, 
                    numrel, 
                    clave_acceso, 
                    importe_total
                )

                # Ejecutar la consulta de inserción
                cursor.execute(insert_query, data)

                # Confirmar la transacción
                conn.commit()
                # Cerrar la conexión
                conn.close()

            except pyodbc.Error as e:
                # Imprimir mensaje de error en caso de fallar la inserción
                print("Error al insertar datos en la tabla SRI_CABRETXMLRECIBIDO:", e)
                errores_insercion.append(autorizacion + "\n")

                    
            # Extraer información del Grupo Movimientos
            movimientos = comprobante_root.findall(".//docsSustento/docSustento")
            for movimiento in movimientos:
                # Extrae información general del documento sustento
                codDocSustento = movimiento.find(".//codDocSustento").text
                numDocSustento = movimiento.find(".//numDocSustento").text
                fechaEmisionDocSustento = movimiento.find(".//fechaEmisionDocSustento").text

                # Itera sobre cada 'retencion' dentro del elemento 'retenciones'
                retenciones = movimiento.findall(".//retenciones/retencion")
                for retencion in retenciones:
                    codigo = retencion.find(".//codigo").text
                    codigoRetencion = retencion.find(".//codigoRetencion").text
                    baseImponible = retencion.find(".//baseImponible").text
                    porcentajeRetener = retencion.find(".//porcentajeRetener").text
                    valorRetenido = retencion.find(".//valorRetenido").text
                
                # Insertar datos en la tabla SRI_movXMLRECIBIDO
                try:
                    # Establecer la conexión
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()

                    # Insertar datos en la tabla sri_movretxmlrecibido
                    insert_query = """
                        INSERT INTO sri_movretxmlrecibido (
                            AUTORIZACION, 
                            CODIGO, 
                            CODIGORETENCION, 
                            BASEIMPONIBLE, 
                            PORCENTAJERETENCION, 
                            VALORRETENIDO, 
                            CODDOCSUSTENTO, 
                            NUMDOCSUSTENTO, 
                            FECHAEMISIONDOCSUSTENTO
                        ) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """

                    # Preparar los datos de las retenciones para la inserción
                    for retencion in retenciones:
                        codigo = retencion.find(".//codigo").text
                        codigoRetencion = retencion.find(".//codigoRetencion").text
                        baseImponible = retencion.find(".//baseImponible").text
                        porcentajeRetener = retencion.find(".//porcentajeRetener").text
                        valorRetenido = retencion.find(".//valorRetenido").text

                        # Datos para la inserción
                        data = (
                            autorizacion,
                            codigo, 
                            codigoRetencion,
                            baseImponible, 
                            porcentajeRetener,
                            valorRetenido,
                            codDocSustento, 
                            numDocSustento,
                            fechaEmisionDocSustento
                        )

                        # Ejecutar la consulta de inserción
                        cursor.execute(insert_query, data)

                    # Confirmar la transacción
                    conn.commit()
                    # Cerrar la conexión
                    conn.close()
                except pyodbc.Error as e:
                    print("Error al insertar datos en la tabla SRI_movXMLRECIBIDO:", e)
                    errores_insercion.append(autorizacion + "\n")

                    
    # Imprimir los números de autorización con problemas de inserción
    if errores_insercion:
        print("Existieron problemas en la inserción. Verifique los siguientes archivos:")
        for autorizacion in errores_insercion:
            print(autorizacion)
            