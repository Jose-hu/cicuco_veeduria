"""
Script para migrar todos los datos locales (SQLite) a Supabase.
Uso:
    python migrate_to_supabase.py
"""
import os
import sys
import sqlite3
from dotenv import load_dotenv

# Asegurar codificacion UTF-8 en consola Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vqyadlmrrdbkloyutvlf.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

if not SUPABASE_KEY:
    print("\n" + "="*70)
    print("[!] AVISO: Falta la API Key de Supabase (SUPABASE_KEY).")
    print("="*70)
    print("Para conectar con tu proyecto:")
    print("1. Ingresa a: https://supabase.com/dashboard/project/vqyadlmrrdbkloyutvlf/settings/api")
    print("2. Copia la clave 'anon' 'public' o la clave 'service_role'")
    print("3. Pégala en el archivo .env en la línea: SUPABASE_KEY=tu_clave_aqui")
    print("4. Vuelve a ejecutar: python migrate_to_supabase.py\n")
    sys.exit(1)

try:
    from supabase import create_client, Client
except ImportError:
    print("Instalando biblioteca supabase...")
    os.system("pip install supabase")
    from supabase import create_client, Client

print(f"[*] Conectando a Supabase ({SUPABASE_URL})...")
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"[-] Error al inicializar cliente Supabase: {e}")
    sys.exit(1)

db_path = os.path.join(os.path.dirname(__file__), "veeduria.db")
if not os.path.exists(db_path):
    print(f"[-] Base de datos local {db_path} no encontrada.")
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n[+] Iniciando migración de datos hacia Supabase...")

# 1. Migrar Contratos
try:
    cursor.execute("SELECT * FROM contracts")
    contracts = [dict(row) for row in cursor.fetchall()]
    print(f"[*] Encontrados {len(contracts)} contratos locales.")
    for c in contracts:
        c_data = dict(c)
        res = supabase.table("contracts").upsert(c_data, on_conflict="code").execute()
    print("[+] Contratos migrados exitosamente a Supabase.")
except Exception as e:
    print(f"[-] Error al migrar contratos: {e}")

# 2. Migrar Reportes / Denuncias
try:
    cursor.execute("SELECT * FROM reports")
    reports = [dict(row) for row in cursor.fetchall()]
    print(f"[*] Encontrados {len(reports)} reportes/denuncias locales.")
    for r in reports:
        r_data = dict(r)
        res = supabase.table("reports").upsert(r_data, on_conflict="code").execute()
    print("[+] Reportes y denuncias migrados exitosamente a Supabase.")
except Exception as e:
    print(f"[-] Error al migrar reportes: {e}")

# 3. Migrar Configuraciones
try:
    cursor.execute("SELECT * FROM settings")
    settings = [dict(row) for row in cursor.fetchall()]
    print(f"[*] Encontradas {len(settings)} configuraciones locales.")
    for s in settings:
        s_data = dict(s)
        res = supabase.table("settings").upsert(s_data, on_conflict="key").execute()
    print("[+] Configuraciones migradas exitosamente a Supabase.")
except Exception as e:
    print(f"[-] Error al migrar configuraciones: {e}")

conn.close()
print("\n" + "="*70)
print("[+] MIGRACION COMPLETADA CON EXITO!")
print("Tus datos locales ya están respaldados y sincronizados en Supabase.")
print("="*70 + "\n")
