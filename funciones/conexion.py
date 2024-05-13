def obtener_conexion():
    # Lee las variables de conexión desde el archivo
    with open('conexion.txt', 'r') as file:
        config_data = file.readlines()

    # Inicializa las variables
    server = ''
    database = ''
    username = ''
    password = ''

    # Parsea las variables desde el archivo
    for line in config_data:
        key, value = line.strip().split('=')
        if key == 'server':
            server = value
        elif key == 'database':
            database = value
        elif key == 'username':
            username = value
        elif key == 'password':
            password = value

    # Construye la cadena de conexión
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    return conn_str
