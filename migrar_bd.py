import sqlite3
import os

# Ruta completa de tu base de datos
db_path = r"C:\Users\Asesor Comercial\Desktop\RA PERSONAL\TMIMPORT_WEB\clientes.db"

# Verificar si la base existe
if not os.path.exists(db_path):
    print("⚠️ No se encontró el archivo clientes.db en la ruta indicada.")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 1. Renombrar la tabla actual
    cursor.execute("ALTER TABLE usuarios RENAME TO usuarios_old;")

    # 2. Crear la nueva tabla con 'contrasena' en lugar de 'contraseña'
    cursor.execute("""
    CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        contrasena TEXT
    )
    """)

    # 3. Migrar los datos
    cursor.execute("""
    INSERT INTO usuarios (id, usuario, contrasena)
    SELECT id, usuario, contraseña FROM usuarios_old;
    """)

    # 4. Eliminar la tabla antigua
    cursor.execute("DROP TABLE usuarios_old;")

    conn.commit()
    print("✅ Migración completada. Ahora la columna se llama 'contrasena'.")

except sqlite3.Error as e:
    print("❌ Error durante la migración:", e)

finally:
    conn.close()