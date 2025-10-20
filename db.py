import pymysql.cursors
import sys


def obtenerConexion(host='localhost', port=3339, user='root', password='', database='bd_eduquiz'):
    """Devuelve una conexión pymysql configurada con DictCursor.
    Los parámetros tienen valores por defecto; se pueden cambiar desde .env antes de usar.
    """
    try:
        connection = pymysql.connect(host=host,
                                     port=port,
                                     user=user,
                                     password=password,
                                     database=database,
                                     cursorclass=pymysql.cursors.DictCursor)
        return connection
    except Exception as e:
        print("Error al obtener la conexión: %s" % (repr(e)), file=sys.stderr)
        return None


# Helpers genéricos (puedes migrar las versiones completas desde main.py cuando estés listo)

def insertar_item(conexion, tabla, nombre, url_imagen, precio):
    try:
        with conexion.cursor() as cursor:
            sql = f"INSERT INTO `{tabla}` (`nombre`, `url_imagen`, `precio`) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre, url_imagen, precio))
            conexion.commit()
            return True, cursor.lastrowid
    except Exception as e:
        return False, str(e)


def obtener_items_crud(conexion, tabla, id_columna):
    try:
        with conexion.cursor() as cursor:
            sql = f"SELECT {id_columna} AS id, nombre, url_imagen, precio FROM {tabla} WHERE vigencia = 1 ORDER BY {id_columna} ASC"
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        return []


def obtener_item_por_id(conexion, tabla, columna_id, id_item):
    try:
        with conexion.cursor() as cursor:
            sql = f"SELECT {columna_id} AS id, nombre, url_imagen, precio FROM `{tabla}` WHERE `{columna_id}` = %s"
            cursor.execute(sql, (id_item,))
            return cursor.fetchone()
    except Exception as e:
        return None
