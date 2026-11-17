from getpass import getpass
from werkzeug.security import generate_password_hash
from config import Config
import mysql.connector

nombre = input("Nombre del administrador: ").strip()
correo = input("Correo del administrador: ").strip().lower()
password = getpass("Contraseña (mínimo 10 caracteres): ")

if not nombre or not correo or len(password) < 10:
    raise SystemExit("Datos incompletos o contraseña demasiado corta.")

conn = mysql.connector.connect(
    host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
    password=Config.DB_PASSWORD, database=Config.DB_NAME
)
cur = conn.cursor()
try:
    cur.execute(
        """INSERT INTO usuarios (nombre,correo,password_hash,rol,estado)
           VALUES (%s,%s,%s,'administrador',1)""",
        (nombre, correo, generate_password_hash(password))
    )
    conn.commit()
    print("Administrador creado correctamente.")
except mysql.connector.IntegrityError:
    conn.rollback()
    print("Ese correo ya existe.")
finally:
    cur.close()
    conn.close()
