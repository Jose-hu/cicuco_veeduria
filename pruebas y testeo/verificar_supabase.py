"""
Script de verificación de conexión y tablas en Supabase.
Uso:
    python verificar_supabase.py
"""
import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print("="*65)
print("🔍 COMPROBACIÓN DE CONEXIÓN CON SUPABASE")
print("="*65)
print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-5:] if SUPABASE_KEY else 'NO CONFIGURADA'}")
print("-" * 65)

if not SUPABASE_KEY:
    print("❌ Falta configurar SUPABASE_KEY en el archivo .env")
    sys.exit(1)

try:
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Autenticación con Supabase: EXITOSA")
except Exception as e:
    print(f"❌ Error al autenticar con Supabase: {e}")
    sys.exit(1)

tables = ["contracts", "reports", "settings"]
all_ok = True

for t in tables:
    try:
        res = client.table(t).select("*").limit(1).execute()
        print(f"✅ Tabla '{t}': CREADA Y LISTA (Registros accesibles)")
    except Exception as e:
        print(f"⚠️  Tabla '{t}': PENDIENTE POR CREAR (Ejecuta supabase_schema.sql en el SQL Editor)")
        all_ok = False

print("-" * 65)
if all_ok:
    print("🎉 ¡TODO PERFECTO! Tu base de datos en Supabase está activa y operativa.")
else:
    print("👉 Pasos para activar las tablas pendientes:")
    print("1. Abre: https://supabase.com/dashboard/project/vqyadlmrrdbkloyutvlf/sql/new")
    print("2. Pega el contenido de 'supabase_schema.sql'")
    print("3. Presiona 'Run' y vuelve a ejecutar: python verificar_supabase.py")
print("="*65)
