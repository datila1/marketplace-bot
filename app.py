import os
import json
from flask import Flask, request, jsonify
from groq import Groq
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
FACEBOOK_VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Configuración del negocio
BUSINESS_CONFIG = {
    'name': os.getenv('BUSINESS_NAME', 'Tu Nombre'),
    'whatsapp': os.getenv('WHATSAPP_NUMBER', '70123456'),
    'product': os.getenv('PRODUCT_NAME', 'tappers'),
    'price': os.getenv('PRODUCT_PRICE', '35'),
    'delivery_zone': os.getenv('DELIVERY_ZONE', '4to anillo'),
    'delivery_cost': os.getenv('DELIVERY_COST_OUTSIDE', '15')
}

# Cliente Groq con manejo de errores
try:
    client = Groq(api_key=GROQ_API_KEY)
    print("Groq client initialized successfully")
except Exception as e:
    print(f"Error initializing Groq: {e}")
    client = None

# Almacenamiento temporal de conversaciones (en producción usar base de datos)
conversations = {}

def get_ai_response(user_message, user_id):
    """Genera respuesta usando Groq AI"""
    
    # Verificar si el cliente está disponible
    if client is None:
        return "Disculpa, el servicio de respuestas automáticas no está disponible en este momento. Por favor contacta por WhatsApp."
    
    # Obtener historial de conversación
    if user_id not in conversations:
        conversations[user_id] = []
    
    # Prompt del sistema con información del negocio
    system_prompt = f"""Eres {BUSINESS_CONFIG['name']}, vendedor de {BUSINESS_CONFIG['product']} en Facebook Marketplace.

Información de tu negocio:
- Producto: {BUSINESS_CONFIG['product']}
- Precio: {BUSINESS_CONFIG['price']} bs por unidad
- Envío gratis dentro del {BUSINESS_CONFIG['delivery_zone']}
- Envío fuera de la zona: +{BUSINESS_CONFIG['delivery_cost']} bs
- WhatsApp: {BUSINESS_CONFIG['whatsapp']}

INSTRUCCIONES IMPORTANTES:
1. Responde de manera natural y conversacional, como una persona real
2. Sé directo
3. Solo proporciona el WhatsApp cuando el cliente esté listo para comprar
4. Si preguntan por ubicación para envío, da el WhatsApp para coordinar
5. Mantén respuestas cortas y naturales
6. Si el cliente parece decidido a comprar, proporciónale el WhatsApp

Ejemplos de respuestas naturales:
- "Los {BUSINESS_CONFIG['product']} están a {BUSINESS_CONFIG['price']} bs"
- "Perfecto! Mi WhatsApp es {BUSINESS_CONFIG['whatsapp']}, mándame tu ubicación"
- "Sí hago envíos, dentro del {BUSINESS_CONFIG['delivery_zone']} es gratis"

Responde SOLO como el vendedor, nunca expliques que eres una IA."""

    try:
        # Agregar mensaje del usuario al historial
        conversations[user_id].append({"role": "user", "content": user_message})
        
        # Preparar mensajes para la IA
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversations[user_id][-10:])  # Últimos 10 mensajes
        
        # Llamada a Groq
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=150
        )
        
        ai_response = chat_completion.choices[0].message.content
        
        # Agregar respuesta de la IA al historial
        conversations[user_id].append({"role": "assistant", "content": ai_response})
        
        return ai_response
        
    except Exception as e:
        print(f"Error con Groq AI: {e}")
        return "Disculpa, en este momento tengo problemas técnicos. ¿Podrías intentar de nuevo?"

def send_facebook_message(recipient_id, message_text):
    """Envía mensaje a Facebook Messenger"""
    url = f"https://graph.facebook.com/v18.0/me/messages"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verificación del webhook de Facebook"""
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if token == FACEBOOK_VERIFY_TOKEN:
        return challenge
    return 'Token de verificación incorrecto', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibe mensajes de Facebook Messenger"""
    data = request.get_json()
    
    try:
        # Procesar mensajes entrantes
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if 'message' in messaging_event:
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text', '')
                    
                    if message_text:  # Solo procesar mensajes de texto
                        print(f"Mensaje recibido de {sender_id}: {message_text}")
                        
                        # Generar respuesta con IA
                        ai_response = get_ai_response(message_text, sender_id)
                        
                        # Enviar respuesta
                        send_facebook_message(sender_id, ai_response)
                        
                        print(f"Respuesta enviada: {ai_response}")
                        
                        # Notificación especial si menciona WhatsApp (cliente listo para comprar)
                        if 'whatsapp' in ai_response.lower():
                            print(f"🚨 CLIENTE LISTO PARA COMPRAR: {sender_id}")
                            # Aquí puedes agregar notificación push, email, etc.
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Error procesando webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba"""
    return jsonify({
        "status": "Bot funcionando correctamente",
        "business": BUSINESS_CONFIG['name'],
        "product": BUSINESS_CONFIG['product'],
        "groq_status": "connected" if client else "disconnected"
    })

@app.route('/conversations', methods=['GET'])
def get_conversations():
    """Ver conversaciones activas (para debug)"""
    return jsonify(conversations)

@app.route('/', methods=['GET'])
def home():
    """Página de inicio"""
    return jsonify({
        "message": "Bot de Marketplace funcionando",
        "status": "online",
        "business": BUSINESS_CONFIG['name']
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
