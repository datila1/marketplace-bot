#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def main():
    print("DIAGNOSTICO FACEBOOK MESSENGER BOT")
    print("=" * 50)
    
    # Verificar tokens
    page_token = os.getenv('PAGE_ACCESS_TOKEN', '')
    app_secret = os.getenv('FACEBOOK_APP_SECRET', '')
    verify_token = os.getenv('VERIFY_TOKEN', '')
    
    print(f"PAGE_ACCESS_TOKEN: {'OK' if page_token else 'FALTANTE'} ({len(page_token)} chars)")
    print(f"FACEBOOK_APP_SECRET: {'OK' if app_secret else 'FALTANTE'} ({len(app_secret)} chars)")  
    print(f"VERIFY_TOKEN: {'OK' if verify_token else 'FALTANTE'}")
    print()
    
    # Verificar token de página
    if page_token:
        try:
            url = f"https://graph.facebook.com/me?access_token={page_token}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"TOKEN VALIDO - Pagina: {data.get('name', 'Sin nombre')}")
            else:
                print(f"TOKEN INVALIDO - Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"ERROR verificando token: {e}")
    
    # Verificar webhook local
    try:
        url = "http://localhost:5000/webhook"
        params = {
            'hub.mode': 'subscribe',
            'hub.challenge': 'test123',
            'hub.verify_token': 'mi_token_secreto_marketplace_2024'
        }
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            print("WEBHOOK LOCAL: OK")
        else:
            print(f"WEBHOOK LOCAL: ERROR {response.status_code}")
    except Exception as e:
        print(f"WEBHOOK LOCAL: ERROR - {e}")
    
    print()
    print("INSTRUCCIONES:")
    print("1. Si todos los tokens estan OK, ejecutar: ngrok http 5000")
    print("2. Configurar webhook en Facebook con URL de ngrok + /webhook")
    print("3. Probar enviando mensaje a la pagina")

if __name__ == "__main__":
    main()