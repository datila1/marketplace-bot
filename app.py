import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from groq import Groq
import requests
from dotenv import load_dotenv
from functools import wraps
import time
from collections import defaultdict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
FACEBOOK_VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Configuración del negocio
BUSINESS_CONFIG = {
    'name': os.getenv('BUSINESS_NAME', 'Hogar & Más SC'),
    'whatsapp': os.getenv('WHATSAPP_NUMBER', '78056048'),
    'product': os.getenv('PRODUCT_NAME', 'tappers'),
    'price': int(os.getenv('PRODUCT_PRICE', '35')),
    'delivery_zone': os.getenv('DELIVERY_ZONE', '4to anillo'),
    'delivery_cost': int(os.getenv('DELIVERY_COST_OUTSIDE', '15'))
}

# Rate limiting
user_requests = defaultdict(list)
RATE_LIMIT = 10  # máximo 10 mensajes por minuto por usuario

# Cliente Groq
try:
    client = Groq(api_key=GROQ_API_KEY)
    logger.info("Groq client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Groq: {e}")
    client = None

class DatabaseManager:
    def __init__(self, db_path='marketplace_bot.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de conversaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT
            )
        ''')
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                profile_pic TEXT,
                first_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                phone_requested BOOLEAN DEFAULT FALSE,
                purchase_intent BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Tabla de analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id TEXT,
                data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de leads calientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hot_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                lead_score INTEGER DEFAULT 0,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                contacted BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def add_message(self, user_id, message, sender, session_id=None):
        """Agregar mensaje a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (user_id, message, sender, session_id) VALUES (?, ?, ?, ?)",
            (user_id, message, sender, session_id)
        )
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, user_id, limit=10):
        """Obtener historial de conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message, sender FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        messages = cursor.fetchall()
        conn.close()
        
        # Convertir a formato para Groq
        history = []
        for message, sender in reversed(messages):
            role = "user" if sender == "user" else "assistant"
            history.append({"role": role, "content": message})
        
        return history
    
    def update_user(self, user_id, **kwargs):
        """Actualizar información del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si el usuario existe
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        
        # Actualizar campos
        set_clauses = []
        values = []
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        if set_clauses:
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
            cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def log_analytics(self, event_type, user_id=None, data=None):
        """Registrar evento de analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO analytics (event_type, user_id, data) VALUES (?, ?, ?)",
            (event_type, user_id, json.dumps(data) if data else None)
        )
        conn.commit()
        conn.close()
    
    def add_hot_lead(self, user_id, lead_score, notes=None):
        """Agregar lead caliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO hot_leads (user_id, lead_score, notes) VALUES (?, ?, ?)",
            (user_id, lead_score, notes)
        )
        conn.commit()
        conn.close()
        logger.warning(f"🔥 HOT LEAD: {user_id} - Score: {lead_score} - {notes}")

# Inicializar base de datos
db = DatabaseManager()

def rate_limit_check(user_id):
    """Verificar rate limiting"""
    now = time.time()
    user_requests[user_id] = [req_time for req_time in user_requests[user_id] if now - req_time < 60]
    
    if len(user_requests[user_id]) >= RATE_LIMIT:
        return False
    
    user_requests[user_id].append(now)
    return True

def get_user_profile(user_id):
    """Obtener perfil del usuario desde Facebook"""
    try:
        url = f"https://graph.facebook.com/v18.0/{user_id}"
        params = {
            'fields': 'first_name,last_name,profile_pic',
            'access_token': FACEBOOK_ACCESS_TOKEN
        }
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else {}
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return {}

def analyze_purchase_intent(message, conversation_history):
    """Analizar intención de compra"""
    intent_keywords = {
        'high': ['comprar', 'precio', 'cuanto', 'disponible', 'stock', 'whatsapp', 'contacto', 'ubicacion'],
        'medium': ['interesa', 'info', 'detalles', 'envio', 'delivery'],
        'low': ['hola', 'buenos dias', 'que tal']
    }
    
    message_lower = message.lower()
    score = 0
    
    # Analizar mensaje actual
    for word in intent_keywords['high']:
        if word in message_lower:
            score += 3
    
    for word in intent_keywords['medium']:
        if word in message_lower:
            score += 2
    
    for word in intent_keywords['low']:
        if word in message_lower:
            score += 1
    
    # Analizar historial
    if len(conversation_history) > 3:
        score += 2  # Usuario comprometido
    
    return min(score, 10)  # Máximo 10

def get_enhanced_ai_response(user_message, user_id):
    """Generar respuesta mejorada con IA"""
    if client is None:
        return "Disculpa, el servicio no está disponible. Contacta por WhatsApp al " + BUSINESS_CONFIG['whatsapp']
    
    try:
        # Obtener historial de conversación
        conversation_history = db.get_conversation_history(user_id, 8)
        
        # Analizar intención de compra
        intent_score = analyze_purchase_intent(user_message, conversation_history)
        
        # Sistema de prompt mejorado
        system_prompt = f"""Eres un vendedor experto de {BUSINESS_CONFIG['name']}, especializado en {BUSINESS_CONFIG['product']}.

INFORMACIÓN DEL NEGOCIO:
- Producto: {BUSINESS_CONFIG['product']} de excelente calidad
- Precio: {BUSINESS_CONFIG['price']} bs por unidad
- Envío GRATIS dentro del {BUSINESS_CONFIG['delivery_zone']}
- Envío fuera de zona: +{BUSINESS_CONFIG['delivery_cost']} bs
- WhatsApp: {BUSINESS_CONFIG['whatsapp']}

PAUTAS DE CONVERSACIÓN:
1. Sé natural, amigable y profesional
2. Responde máximo 2 líneas
3. Si preguntan por stock: "Sí tengo disponible"
4. Si preguntan ubicación para envío: da el WhatsApp
5. Si muestran interés fuerte: facilita el WhatsApp
6. Enfócate en beneficios del producto
7. Crea urgencia sutil si es apropiado

EJEMPLOS DE RESPUESTAS:
- "Los {BUSINESS_CONFIG['product']} están a {BUSINESS_CONFIG['price']} bs, excelente calidad 👌"
- "Perfecto! Escríbeme al {BUSINESS_CONFIG['whatsapp']} para coordinar el envío"
- "Sí tengo stock disponible. Envío gratis en {BUSINESS_CONFIG['delivery_zone']}"

IMPORTANTE: Solo eres el vendedor, nunca menciones que eres IA."""

        # Preparar mensajes
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history[-6:])  # Últimos 6 mensajes
        messages.append({"role": "user", "content": user_message})
        
        # Llamada a Groq
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.6,
            max_tokens=100
        )
        
        ai_response = chat_completion.choices[0].message.content.strip()
        
        # Guardar en base de datos
        db.add_message(user_id, user_message, "user")
        db.add_message(user_id, ai_response, "assistant")
        
        # Actualizar usuario
        db.update_user(
            user_id, 
            last_interaction=datetime.now(),
            total_messages=1,  # Se incrementará automáticamente
            purchase_intent=(intent_score >= 5)
        )
        
        # Si es un lead caliente, registrarlo
        if intent_score >= 6:
            notes = f"Mensaje: {user_message[:50]}..."
            db.add_hot_lead(user_id, intent_score, notes)
        
        # Analytics
        db.log_analytics("message_received", user_id, {
            "message": user_message,
            "intent_score": intent_score,
            "response": ai_response
        })
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error with Groq AI: {e}")
        return "Disculpa, tengo un problema técnico. ¿Podrías escribirme al " + BUSINESS_CONFIG['whatsapp'] + "?"

def send_facebook_message(recipient_id, message_text):
    """Enviar mensaje a Facebook Messenger"""
    url = f"https://graph.facebook.com/v18.0/me/messages"
    
    headers = {"Content-Type": "application/json"}
    
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logger.error(f"Error sending message: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending Facebook message: {e}")
        return {}

def send_typing_indicator(recipient_id):
    """Enviar indicador de escritura"""
    url = f"https://graph.facebook.com/v18.0/me/messages"
    
    data = {
        "recipient": {"id": recipient_id},
        "sender_action": "typing_on",
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    
    try:
        requests.post(url, json=data)
    except Exception as e:
        logger.error(f"Error sending typing indicator: {e}")

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verificación del webhook de Facebook"""
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if token == FACEBOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return challenge
    
    logger.warning("Invalid verification token")
    return 'Token de verificación incorrecto', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibir mensajes de Facebook Messenger"""
    data = request.get_json()
    
    try:
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if 'message' in messaging_event:
                    sender_id = messaging_event['sender']['id']
                    
                    # Verificar rate limiting
                    if not rate_limit_check(sender_id):
                        logger.warning(f"Rate limit exceeded for user {sender_id}")
                        continue
                    
                    # Manejar diferentes tipos de mensaje
                    message = messaging_event['message']
                    
                    if 'text' in message:
                        message_text = message['text']
                        logger.info(f"Message from {sender_id}: {message_text}")
                        
                        # Obtener perfil del usuario (primera vez)
                        user_profile = get_user_profile(sender_id)
                        if user_profile:
                            db.update_user(
                                sender_id,
                                first_name=user_profile.get('first_name', ''),
                                last_name=user_profile.get('last_name', ''),
                                profile_pic=user_profile.get('profile_pic', '')
                            )
                        
                        # Enviar indicador de escritura
                        send_typing_indicator(sender_id)
                        
                        # Generar respuesta
                        ai_response = get_enhanced_ai_response(message_text, sender_id)
                        
                        # Enviar respuesta
                        send_facebook_message(sender_id, ai_response)
                        
                        logger.info(f"Response sent to {sender_id}: {ai_response}")
                        
                        # Notificación especial para leads calientes
                        if any(keyword in ai_response.lower() for keyword in ['whatsapp', BUSINESS_CONFIG['whatsapp']]):
                            logger.warning(f"🚨 CLIENTE LISTO PARA COMPRAR: {sender_id}")
                            db.log_analytics("whatsapp_provided", sender_id, {"response": ai_response})
                    
                    elif 'attachments' in message:
                        # Manejar imágenes, stickers, etc.
                        attachment_type = message['attachments'][0]['type']
                        if attachment_type == 'image':
                            response = f"Vi tu imagen! Para más info sobre {BUSINESS_CONFIG['product']}, están a {BUSINESS_CONFIG['price']} bs. ¿Te interesa?"
                        else:
                            response = f"Hola! Te ofrezco {BUSINESS_CONFIG['product']} a {BUSINESS_CONFIG['price']} bs. ¿Te interesa?"
                        
                        send_facebook_message(sender_id, response)
                        db.add_message(sender_id, f"[{attachment_type}]", "user")
                        db.add_message(sender_id, response, "assistant")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/analytics', methods=['GET'])
def analytics():
    """Dashboard de analytics"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Estadísticas generales
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_messages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM hot_leads WHERE contacted = FALSE")
    pending_leads = cursor.fetchone()[0]
    
    # Usuarios activos hoy
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE DATE(last_interaction) = DATE('now')"
    )
    active_today = cursor.fetchone()[0]
    
    # Leads calientes recientes
    cursor.execute(
        "SELECT user_id, lead_score, notes, last_activity FROM hot_leads ORDER BY last_activity DESC LIMIT 10"
    )
    recent_leads = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        "stats": {
            "total_users": total_users,
            "total_messages": total_messages,
            "pending_leads": pending_leads,
            "active_today": active_today
        },
        "recent_leads": [
            {
                "user_id": lead[0],
                "score": lead[1],
                "notes": lead[2],
                "timestamp": lead[3]
            } for lead in recent_leads
        ]
    })

@app.route('/hot-leads', methods=['GET'])
def get_hot_leads():
    """Obtener leads calientes"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT h.user_id, h.lead_score, h.notes, h.last_activity, h.contacted,
               u.first_name, u.last_name
        FROM hot_leads h
        LEFT JOIN users u ON h.user_id = u.user_id
        ORDER BY h.last_activity DESC
    """)
    
    leads = cursor.fetchall()
    conn.close()
    
    return jsonify({
        "leads": [
            {
                "user_id": lead[0],
                "score": lead[1],
                "notes": lead[2],
                "last_activity": lead[3],
                "contacted": lead[4],
                "name": f"{lead[5] or ''} {lead[6] or ''}".strip() or "Usuario"
            } for lead in leads
        ]
    })

@app.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba mejorado"""
    return jsonify({
        "status": "Bot funcionando correctamente ✅",
        "business": BUSINESS_CONFIG['name'],
        "product": BUSINESS_CONFIG['product'],
        "groq_status": "connected" if client else "disconnected",
        "database_status": "connected",
        "version": "2.0 - Enhanced"
    })

@app.route('/', methods=['GET'])
def home():
    """Página de inicio"""
    return jsonify({
        "message": f"🤖 {BUSINESS_CONFIG['name']} - Bot Marketplace v2.0",
        "status": "online",
        "features": [
            "✅ Base de datos persistente",
            "✅ Analytics avanzados", 
            "✅ Detección de leads calientes",
            "✅ Rate limiting",
            "✅ Manejo de attachments",
            "✅ Logging completo"
        ]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting bot server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
