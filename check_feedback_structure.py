import pymysql

# Conexión a la base de datos
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Sebas3120',
    database='chatter_ai_db'
)

try:
    with connection.cursor() as cursor:
        # Ejecutar el comando para describir la tabla feedback
        cursor.execute("DESCRIBE feedback;")
        result = cursor.fetchall()
        for row in result:
            print(row)
finally:
    connection.close()
