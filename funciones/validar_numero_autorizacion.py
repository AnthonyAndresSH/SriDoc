import pyodbc

def buscar_en_base_de_datos(numero_autorizacion, pconn):
    try:
        conn = pyodbc.connect(pconn)
        cursor = conn.cursor()        
        cursor.execute("SELECT COUNT(*) FROM SRI_CABXMLRECIBIDO WHERE AUTORIZACION = ?", numero_autorizacion)
        row = cursor.fetchone()
        if row[0] > 0:
            print("El registro existe en la base de datos.")
            return True
        else:
            print("El registro no existe en la base de datos.")
            return False
    except pyodbc.Error as e:
        print("Error al buscar en la base de datos:", e)
        return False


def validar_numero_autorizacion(numero_autorizacion, pconn):
    # Aquí se invoca la función buscar_en_base_de_datos para determinar si el número de autorización existe
    if buscar_en_base_de_datos(numero_autorizacion, pconn):
        return True
    else:
        return False
    
def buscar_en_base_de_datos_ret(numero_autorizacion, pconn):
    try:
        conn = pyodbc.connect(pconn)
        cursor = conn.cursor()        
        cursor.execute("SELECT COUNT(*) FROM SRI_CABRETXMLRECIBIDO WHERE AUTORIZACION = ?", numero_autorizacion)
        row = cursor.fetchone()
        if row[0] > 0:
            print("El registro existe en la base de datos.")
            return True
        else:
            print("El registro no existe en la base de datos.")
            return False
    except pyodbc.Error as e:
        print("Error al buscar en la base de datos:", e)
        return False


def validar_numero_autorizacion_ret(numero_autorizacion, pconn):
    # Aquí se invoca la función buscar_en_base_de_datos para determinar si el número de autorización existe
    if buscar_en_base_de_datos_ret(numero_autorizacion, pconn):
        return True
    else:
        return False    
