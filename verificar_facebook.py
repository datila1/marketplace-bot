#!/usr/bin/env python3
"""
Script para verificar la configuración de Facebook Messenger
"""

import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_tokens():
    """Verificar que los tokens estén configurados"""
    print("VERIFICACION DE TOKENS")
    print("=" * 50)
    
    page_token = os.getenv('PAGE_ACCESS_TOKEN', '')
    app_secret = os.getenv('FACEBOOK_APP_SECRET', '')
    verify_token = os.getenv('VERIFY_TOKEN', '')
    
    print(f"PAGE_ACCESS_TOKEN: {'Configurado' if page_token else 'FALTANTE'} ({len(page_token)} caracteres)")
    print(f"FACEBOOK_APP_SECRET: {'Configurado' if app_secret else 'FALTANTE'} ({len(app_secret)} caracteres)")  
    print(f"VERIFY_TOKEN: {'Configurado' if verify_token else 'FALTANTE'} ({verify_token})")
    print()
    
    return page_token, app_secret, verify_token

def verificar_page_token(token):
    """Verificar que el PAGE_ACCESS_TOKEN sea válido"""
    print("📄 VERIFICACIÓN DEL PAGE TOKEN")
    print("=" * 50)
    
    if not token:
        print("❌ No hay PAGE_ACCESS_TOKEN configurado")
        return False
        
    try:
        # Verificar token con la API de Facebook
        url = f"https://graph.facebook.com/me?access_token={token}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token válido para página: {data.get('name', 'Sin nombre')}")
            print(f"   ID: {data.get('id', 'Sin ID')}")
            return True
        else:
            print(f"❌ Token inválido: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando token: {e}")
        return False

def verificar_webhook_local():
    """Verificar que el webhook local funcione"""
    print("🌐 VERIFICACIÓN WEBHOOK LOCAL")
    print("=" * 50)
    
    try:
        # Probar webhook local
        url = "http://localhost:5000/webhook"
        params = {
            'hub.mode': 'subscribe',
            'hub.challenge': 'test123',
            'hub.verify_token': 'mi_token_secreto_marketplace_2024'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200 and response.text == 'test123':
            print("✅ Webhook local funcionando correctamente")
            return True
        else:
            print(f"❌ Webhook local falló: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando al webhook local: {e}")
        print("   ¿Está el servidor corriendo en puerto 5000?")
        return False

def main():
    print("DIAGNOSTICO FACEBOOK MESSENGER BOT")
    print("=" * 50)
    print()
    
    # Verificar tokens
    page_token, app_secret, verify_token = verificar_tokens()
    
    # Verificar validez del token
    token_valido = verificar_page_token(page_token)
    
    # Verificar webhook local
    webhook_local = verificar_webhook_local()
    
    print("\n📋 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 50)
    print(f"🔐 Tokens configurados: {'✅' if page_token and app_secret else '❌'}")
    print(f"📄 Page token válido: {'✅' if token_valido else '❌'}")
    print(f"🌐 Webhook local: {'✅' if webhook_local else '❌'}")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("=" * 50)
    
    if not (page_token and app_secret):
        print("1. ❌ Configurar tokens en el archivo .env")
    elif not token_valido:
        print("1. ❌ Verificar que el PAGE_ACCESS_TOKEN sea correcto")
    elif not webhook_local:
        print("1. ❌ Asegurarse que el servidor esté corriendo")
    else:
        print("1. ✅ Iniciar ngrok: ngrok http 5000")
        print("2. ✅ Configurar webhook en Facebook con la URL de ngrok")
        print("3. ✅ Probar enviando mensaje a la página")
    
    print("\n💡 COMANDOS ÚTILES:")
    print("- Iniciar ngrok: ngrok http 5000")
    print("- Ver webhook de Facebook: https://developers.facebook.com/apps/")
    print("- Probar bot: Enviar mensaje a la página de Facebook")

if __name__ == "__main__":
    main()