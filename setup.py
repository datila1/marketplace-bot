#!/usr/bin/env python3
"""
Script de configuración para el bot de Marketplace
Automatiza la configuración inicial y verificaciones
"""

import os
import sqlite3
import requests
from dotenv import load_dotenv

def check_environment():
    """Verificar variables de entorno"""
    load_dotenv()
    
    required_vars = [
        'FACEBOOK_ACCESS_TOKEN',
        'FACEBOOK_VERIFY_TOKEN', 
        'FACEBOOK_PAGE_ID',
        'GROQ_API_KEY',
        'BUSINESS_NAME',
        'WHATSAPP_NUMBER',
        'PRODUCT_NAME',
        'PRODUCT_PRICE'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Todas las variables de entorno están configuradas")
    return True

def test_groq_connection():
    """Verificar conexión con Groq"""
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        # Test simple
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hola"}],
            model="llama3-8b-8192",
            max_tokens=10
        )
        
        print("✅ Conexión con Groq exitosa")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando con Groq: {e}")
        return False

def test_facebook_api():
    """Verificar conexión con Facebook API"""
    try:
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        page_id = os.getenv('FACEBOOK_PAGE_ID')
        
        # Verificar token
        url = f"https://graph.facebook.com/v18.0/me"
        params = {'access_token': access_token}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print("✅ Facebook Access Token válido")
            
            # Verificar permisos de página
            url = f"https://graph.facebook.com/v18.0/{page_id}"
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                page_data = response.json()
                print(f"✅ Acceso a página confirmado: {page_data.get('name', 'N/A')}")
                return True
            else:
                print("❌ No se puede acceder a la página de Facebook")
                return False
        else:
            print("❌ Facebook Access Token inválido")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando Facebook API: {e}")
        return False

def setup_database():
    """Configurar base de datos"""
    try:
        from app import DatabaseManager
        db = DatabaseManager()
        print("✅ Base de datos SQLite configurada correctamente")
        
        # Crear algunos datos de prueba
        db.log_analytics("setup", None, {"event": "initial_setup"})
        print("✅ Datos de prueba insertados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        return False

def create_sample_env():
    """Crear archivo .env de ejemplo"""
    sample_env = """# Configuración del Bot de Marketplace - Hogar & Más SC

# Facebook Configuración
FACEBOOK_ACCESS_TOKEN=tu_access_token_aqui
FACEBOOK_VERIFY_TOKEN=mi_token_secreto_123
FACEBOOK_PAGE_ID=tu_page_id_aqui

# Groq API
GROQ_API_KEY=gsk_tu_api_key_aqui

# Configuración del Negocio
BUSINESS_NAME="Hogar & Más SC"
WHATSAPP_NUMBER=78056048
PRODUCT_NAME=tappers
PRODUCT_PRICE=35
DELIVERY_ZONE="4to anillo"
DELIVERY_COST_OUTSIDE=15

# Servidor (opcional)
PORT=5000
"""
    
    if not os.path.exists('.env'):
        with open('.env.example', 'w') as f:
            f.write(sample_env)
        print("✅ Archivo .env.example creado")
        print("   Cópialo a .env y completa tus datos")

def run_diagnostics():
    """Ejecutar diagnósticos completos"""
    print("🔍 Ejecutando diagnósticos del bot...\n")
    
    # Verificar archivo .env
    if not os.path.exists('.env'):
        print("⚠️  Archivo .env no encontrado")
        create_sample_env()
        return False
    
    all_good = True
    
    # Verificar variables de entorno
    if not check_environment():
        all_good = False
    
    print()
    
    # Verificar Groq
    if not test_groq_connection():
        all_good = False
    
    print()
    
    # Verificar Facebook
    if not test_facebook_api():
        all_good = False
    
    print()
    
    # Configurar base de datos
    if not setup_database():
        all_good = False
    
    print("\n" + "="*50)
    
    if all_good:
        print("🎉 ¡Bot configurado correctamente!")
        print("   Puedes iniciar el servidor con: python app.py")
        print("   Dashboard disponible en: http://localhost:5000")
    else:
        print("❌ Hay problemas en la configuración")
        print("   Revisa los errores anteriores y corrige")
    
    return all_good

def show_help():
    """Mostrar ayuda"""
    help_text = """
🤖 Bot de Marketplace - Hogar & Más SC
=====================================

Comandos disponibles:

python setup.py check      - Verificar configuración
python setup.py create-env - Crear archivo .env de ejemplo
python setup.py help       - Mostrar esta ayuda

Pasos para configurar:

1. Crear cuenta en Groq (groq.com) y obtener API key
2. Configurar página de Facebook y obtener tokens
3. Copiar .env.example a .env y completar datos
4. Ejecutar: python setup.py check
5. Si todo está OK, iniciar: python app.py

Para más información, revisa la documentación.
"""
    print(help_text)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            run_diagnostics()
        elif command == "create-env":
            create_sample_env()
        elif command == "help":
            show_help()
        else:
            print(f"Comando desconocido: {command}")
            show_help()
    else:
        run_diagnostics()
