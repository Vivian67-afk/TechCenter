import mysql.connector
from flask import current_app

def get_db():
    """Abre una conexión nueva usando la configuración de Flask."""
    return mysql.connector.connect(
        host=current_app.config["DB_HOST"],
        port=current_app.config["DB_PORT"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        database=current_app.config["DB_NAME"],
        charset="utf8mb4"
    )

def query_one(sql, params=()):
    """Ejecuta una consulta que devuelve como máximo un registro."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def query_all(sql, params=()):
    """Ejecuta una consulta que devuelve varios registros."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def execute(sql, params=()):
    """Ejecuta INSERT, UPDATE o DELETE y devuelve el ID generado si existe."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
