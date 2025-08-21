import os
import json
import sqlite3
import logging
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
import requests
from dotenv import load_dotenv
from functools import wraps
import time
from collections import defaultdict

# Importar Groq con manejo de errores
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Groq no disponible, usando solo respuestas programadas")

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
app.secret_key = os.getenv('SECRET_KEY', 'hogar-mas-secret-key-2024')

# Configuración
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
FACEBOOK_VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Configuración del negocio
BUSINESS_CONFIG = {
    'name': os.getenv('BUSINESS_NAME', 'Hogar & Más SC'),
    'whatsapp': os.getenv('WHATSAPP_NUMBER', '78056048'),
    'delivery_zone': os.getenv('DELIVERY_ZONE', '4to anillo'),
    'delivery_cost_per_ring': int(os.getenv('DELIVERY_COST_PER_RING', '5')),
    'owner_phone': os.getenv('OWNER_PHONE', '78056048')  # Tu teléfono para recibir leads
}

# Rate limiting
user_requests = defaultdict(list)
RATE_LIMIT = 10

class DatabaseManager:
    def __init__(self, db_path='marketplace_bot.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                category TEXT,
                keywords TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
                phone TEXT,
                address TEXT,
                purchase_count INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0,
                last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Tabla de leads calientes (cuando dan teléfono)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hot_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                phone TEXT,
                products_interested TEXT,
                conversation_summary TEXT,
                lead_score INTEGER DEFAULT 5,
                contacted BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de pedidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                phone TEXT,
                products TEXT,
                total_amount REAL,
                delivery_address TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insertar productos de ejemplo
        self.insert_sample_products()
        logger.info("Database initialized successfully")
    
    def insert_sample_products(self):
        """Insertar productos de ejemplo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        
        if count == 0:
            sample_products = [
                ('Tappers', 'Tuppers de calidad para almacenar alimentos', 35.0, 100, 'Cocina', 'taper,tupper,contenedor,recipiente', True),
                ('Vasos Plásticos', 'Vasos resistentes para toda ocasión', 12.0, 50, 'Cocina', 'vaso,copa,plastico', True),
                ('Platos Plásticos', 'Platos duraderos y coloridos', 20.0, 40, 'Cocina', 'plato,plastico,vajilla', True)
            ]
            
            cursor.executemany(
                "INSERT INTO products (name, description, price, stock, category, keywords, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                sample_products
            )
            
        conn.commit()
        conn.close()
    
    def get_all_products(self, active_only=True):
        """Obtener todos los productos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM products WHERE active = TRUE AND stock > 0 ORDER BY name")
        else:
            cursor.execute("SELECT * FROM products ORDER BY name")
        
        products = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': p[0], 'name': p[1], 'description': p[2], 'price': p[3],
                'stock': p[4], 'category': p[5], 'keywords': p[6], 'active': p[7]
            } for p in products
        ]
    
    def search_products(self, query):
        """Buscar productos por nombre o keywords"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_term = query.lower()
        cursor.execute(
            "SELECT * FROM products WHERE (LOWER(name) LIKE ? OR LOWER(keywords) LIKE ?) AND active = TRUE AND stock > 0",
            (f"%{search_term}%", f"%{search_term}%")
        )
        
        products = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': p[0], 'name': p[1], 'description': p[2], 'price': p[3],
                'stock': p[4], 'category': p[5], 'keywords': p[6], 'active': p[7]
            } for p in products
        ]
    
    def add_message(self, user_id, message, sender):
        """Agregar mensaje a la conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (user_id, message, sender) VALUES (?, ?, ?)",
            (user_id, message, sender)
        )
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, user_id, limit=6):
        """Obtener historial de conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message, sender FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        messages = cursor.fetchall()
        conn.close()
        
        history = []
        for message, sender in reversed(messages):
            role = "user" if sender == "user" else "assistant"
            history.append({"role": role, "content": message})
        
        return history
    
    def save_hot_lead(self, user_id, phone, products_interested, conversation_summary):
        """Guardar lead caliente cuando dan teléfono"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hot_leads (user_id, phone, products_interested, conversation_summary) VALUES (?, ?, ?, ?)",
            (user_id, phone, products_interested, conversation_summary)
        )
        lead_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Enviar notificación inmediata
        self.send_lead_notification(phone, products_interested, conversation_summary)
        
        return lead_id
    
    def send_lead_notification(self, phone, products, conversation):
        """Enviar notificación por WhatsApp al dueño"""
        try:
            # Extraer cantidad si está mencionada en la conversación
            quantity_match = re.search(r'(dos|tres|cuatro|cinco|\d+)', conversation.lower())
            quantity = ""
            if quantity_match:
                num_word = quantity_match.group(1)
                if num_word == "dos": quantity = "2"
                elif num_word == "tres": quantity = "3" 
                elif num_word == "cuatro": quantity = "4"
                elif num_word == "cinco": quantity = "5"
                else: quantity = num_word
                
            # Crear mensaje de notificación
            message = f"🔥 LEAD CALIENTE 🔥\n"
            message += f"📱 Teléfono: {phone}\n"
            message += f"🛍️ Productos: {products}\n"
            if quantity:
                message += f"📦 Cantidad: {quantity} unidades\n"
            message += f"💬 Cliente {conversation[-50:]}...\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            logger.warning(f"🚨 LEAD NOTIFICATION: {message}")
            
            # TODO: Implementar envío real por WhatsApp Business API
            # self.send_whatsapp_to_owner(message)
            
        except Exception as e:
            logger.error(f"Error sending lead notification: {e}")

# Inicializar base de datos
db = DatabaseManager()

# Forzar solo respuestas programadas (más confiable)
client = None
logger.info("🎯 Usando SOLO respuestas programadas para máxima confiabilidad")

def extract_phone_number(message):
    """Extraer número de teléfono del mensaje"""
    # Buscar patrones de teléfono boliviano
    patterns = [
        r'\b[67]\d{7}\b',  # 8 dígitos empezando con 6 o 7
        r'\b[67]\d{3}[-\s]?\d{4}\b',  # Con guion o espacio
        r'\+591[-\s]?[67]\d{7}\b'  # Con código de país
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group().replace('-', '').replace(' ', '').replace('+591', '')
    
    return None

def get_objective_response(user_message, user_id):
    """Respuestas objetivas y directas orientadas a venta"""
    message_lower = user_message.lower()
    
    # Debug: log para entender qué está pasando
    logger.info(f"Procesando mensaje: '{user_message}' de usuario {user_id}")
    
    # Extraer teléfono si lo proporciona
    phone = extract_phone_number(user_message)
    if phone:
        # Obtener productos mencionados en la conversación
        conversation = db.get_conversation_history(user_id, 10)
        products_mentioned = []
        total_conversation = " ".join([msg["content"] for msg in conversation])
        
        # Buscar productos mencionados
        all_products = db.get_all_products()
        for product in all_products:
            if product['name'].lower() in total_conversation.lower():
                products_mentioned.append(product['name'])
        
        # Guardar como lead caliente
        products_str = ", ".join(products_mentioned) if products_mentioned else "Productos varios"
        db.save_hot_lead(user_id, phone, products_str, total_conversation[-200:])
        
        return f"Ok, ya te escribo al WhatsApp"
    
    # Buscar productos mencionados
    products = db.search_products(user_message)
    
    # Respuestas súper directas exactamente como especificaste
    if any(word in message_lower for word in ['hola', 'buenos', 'buenas', 'hey']):
        return "Hola! ¿Qué producto necesitas?"
    
    elif any(word in message_lower for word in [
        'taper', 'tapper', 'tappers', 'tupper', 'tuppers', 'tupperware',
        'contenedor', 'contenedores', 'recipiente', 'recipientes', 
        'envase', 'envases', 'hermetico', 'hermeticos', 
        'guardar comida', 'almacenar', 'cocina'
    ]):
        logger.info(f"Detectado producto TAPPERS en mensaje: {message_lower}")
        return "Sí"
    
    elif any(word in message_lower for word in [
        'vaso', 'vasos', 'copa', 'copas', 'beber', 'tomar', 'plastico para beber'
    ]):
        logger.info(f"Detectado producto VASOS en mensaje: {message_lower}")
        return "Sí"
    
    elif any(word in message_lower for word in [
        'plato', 'platos', 'vajilla', 'servir', 'comer', 'plastico para comer'
    ]):
        logger.info(f"Detectado producto PLATOS en mensaje: {message_lower}")
        return "Sí"
    
    elif any(word in message_lower for word in ['precio', 'cuanto', 'cuesta', 'valor', 'a cuanto', 'estan']):
        # Verificar qué producto mencionaron en la conversación reciente
        conversation = db.get_conversation_history(user_id, 8)
        full_conversation = " ".join([msg["content"] for msg in conversation]).lower()
        
        # Debug: mostrar la conversación para entender
        logger.info(f"Historial conversación para {user_id}: {full_conversation}")
        
        # Buscar menciones de productos en orden de prioridad (más palabras)
        if any(word in full_conversation for word in [
            'taper', 'tapper', 'tappers', 'tupper', 'tuppers', 'tupperware',
            'contenedor', 'contenedores', 'recipiente', 'recipientes', 
            'envase', 'envases', 'hermetico', 'guardar comida'
        ]):
            logger.info(f"Detectado producto: Tappers")
            return "35 bs"
        elif any(word in full_conversation for word in [
            'vaso', 'vasos', 'copa', 'copas', 'beber', 'tomar'
        ]):
            logger.info(f"Detectado producto: Vasos")
            return "12 bs"
        elif any(word in full_conversation for word in [
            'plato', 'platos', 'vajilla', 'servir', 'comer'
        ]):
            logger.info(f"Detectado producto: Platos")
            return "20 bs"
        else:
            # Si pregunta precio pero no hay contexto de producto
            logger.info(f"No se detectó producto en conversación")
            return "¿De qué producto?"
    
    elif any(word in message_lower for word in ['menos', 'descuento', 'rebaja', 'barato', 'nada menos']):
        return f"Nada menos 😅, pero incluye delivery hasta {BUSINESS_CONFIG['delivery_zone']}"
    
    elif any(word in message_lower for word in ['dos', 'tres', 'cuatro', 'cinco', 'cantidad']) or any(char.isdigit() for char in user_message):
        # Extraer cantidad
        numbers = re.findall(r'\d+', user_message)
        if numbers:
            quantity = numbers[0]
            return f"Ok. Deme su teléfono"
        else:
            return "¿Cuántos necesitas?"
    
    elif any(word in message_lower for word in ['delivery', 'envio', 'donde', 'ubicacion']):
        return f"Delivery gratis hasta {BUSINESS_CONFIG['delivery_zone']}"
    
    elif any(word in message_lower for word in ['telefono', 'contacto', 'whatsapp', 'numero']):
        return "Deme su número"
    
    elif any(word in message_lower for word in ['quiero', 'compro', 'llevo', 'acepto', 'esta bien', 'ok', 'me da']):
        return "Ok. Deme su teléfono"
    
    elif any(word in message_lower for word in ['que', 'tienes', 'vendes', 'productos', 'catalogo']):
        return "Tappers, vasos, platos. ¿Qué necesita?"
    
    elif any(word in message_lower for word in ['stock', 'disponible', 'hay']):
        return "Sí hay"
    
    else:
        # Si no reconoce nada específico, mostrar catálogo
        logger.info(f"Mensaje no reconocido: {message_lower} - Mostrando catálogo")
        return "Tappers, vasos, platos. ¿Qué necesita?"

def get_enhanced_ai_response(user_message, user_id):
    """Respuesta con IA súper objetiva"""
    if client is None:
        return get_objective_response(user_message, user_id)
    
    try:
        conversation_history = db.get_conversation_history(user_id, 4)
        
        # Sistema prompt súper directo y mejorado
        system_prompt = f"""Eres un vendedor SÚPER DIRECTO de {BUSINESS_CONFIG['name']}. 

PRODUCTOS DISPONIBLES:
- Tappers: 35 bs (palabras clave: taper, tupper, contenedor, recipiente, guardar comida)
- Vasos: 12 bs (palabras clave: vaso, copa, beber)
- Platos: 20 bs (palabras clave: plato, vajilla, servir comida)

REGLAS ESTRICTAS:
1. Máximo 8 palabras por respuesta
2. SÉ SÚPER DIRECTO Y OBJETIVO
3. Si mencionan cualquier sinónimo de un producto, trátalo como ese producto

DETECCIÓN INTELIGENTE:
- "contenedores", "recipientes", "tuppers", "guardar comida" = Tappers
- "vasos", "copas", "beber" = Vasos  
- "platos", "vajilla", "servir" = Platos

RESPUESTAS EXACTAS OBLIGATORIAS:
- Si preguntan "tiene X?": responde solo "Sí"
- Si preguntan precio de producto mencionado: solo el precio "35 bs"
- Si piden descuento: "Nada menos 😅, pero incluye delivery hasta {BUSINESS_CONFIG['delivery_zone']}"
- Si aceptan/quieren comprar: "Ok. Deme su teléfono"  
- Si dan teléfono: "Ok, ya te escribo al WhatsApp"

EJEMPLOS EXACTOS:
Usuario: "tienen contenedores para guardar comida?"
Tú: "Sí"

Usuario: "cuánto cuestan los recipientes?"
Tú: "35 bs"

Usuario: "a cuánto están?"
Tú: "35 bs" (si mencionaron tappers antes)

Usuario: "quiero dos"
Tú: "Ok. Deme su teléfono"

IMPORTANTE: 
- SIEMPRE usa las respuestas exactas de los ejemplos
- NO agregues palabras extra como "excelente", "perfecto"
- SÉ EXACTO Y DIRECTO"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history[-3:])
        messages.append({"role": "user", "content": user_message})
        
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.1,  # Muy bajo para respuestas consistentes
            max_tokens=50    # Máximo 50 tokens para respuestas cortas
        )
        
        ai_response = chat_completion.choices[0].message.content.strip()
        
        # Verificar si dieron teléfono en el mensaje original
        phone = extract_phone_number(user_message)
        if phone:
            conversation = db.get_conversation_history(user_id, 10)
            total_conversation = " ".join([msg["content"] for msg in conversation])
            
            # Analizar productos mencionados
            products_mentioned = []
            if any(word in total_conversation.lower() for word in ['taper', 'tupper', 'contenedor', 'recipiente']):
                products_mentioned.append("Tappers")
            if any(word in total_conversation.lower() for word in ['vaso', 'copa']):
                products_mentioned.append("Vasos")
            if any(word in total_conversation.lower() for word in ['plato']):
                products_mentioned.append("Platos")
            
            products_str = ", ".join(products_mentioned) if products_mentioned else "Productos mencionados en chat"
            db.save_hot_lead(user_id, phone, products_str, total_conversation[-200:])
            
            # Forzar respuesta específica para teléfonos
            ai_response = "Ok, ya te escribo al WhatsApp"
        
        # Guardar en base de datos
        db.add_message(user_id, user_message, "user")
        db.add_message(user_id, ai_response, "assistant")
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error with Groq AI: {e}")
        return get_objective_response(user_message, user_id)

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
        return response.json()
    except Exception as e:
        logger.error(f"Error sending Facebook message: {e}")
        return {}

# WEBHOOK ENDPOINTS
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if token == FACEBOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return challenge
    
    logger.warning("Invalid verification token")
    return 'Token de verificación incorrecto', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    try:
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if 'message' in messaging_event:
                    sender_id = messaging_event['sender']['id']
                    message = messaging_event['message']
                    
                    if 'text' in message:
                        message_text = message['text']
                        logger.info(f"Message from {sender_id}: {message_text}")
                        
                        # Generar respuesta súper directa
                        ai_response = get_enhanced_ai_response(message_text, sender_id)
                        
                        # Enviar respuesta
                        send_facebook_message(sender_id, ai_response)
                        
                        logger.info(f"Response sent to {sender_id}: {ai_response}")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# PANEL ADMIN SIMPLE
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Admin - {{ business_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .btn { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚙️ Panel de Administración</h1>
            <p>{{ business_name }} - Gestión Directa</p>
        </div>
        
        {% if message %}
        <div style="padding: 15px; margin-bottom: 20px; border-radius: 5px; {{ 'background: #d4edda; color: #155724;' if success else 'background: #f8d7da; color: #721c24;' }}">
            {{ message }}
        </div>
        {% endif %}
        
        <h2>➕ Agregar Producto</h2>
        <form method="POST" action="/admin/add">
            <div class="form-group">
                <label>Nombre:</label>
                <input type="text" name="name" required placeholder="Ej: Tappers grandes">
            </div>
            <div class="form-group">
                <label>Precio (Bs):</label>
                <input type="number" name="price" step="0.01" required placeholder="35">
            </div>
            <div class="form-group">
                <label>Stock:</label>
                <input type="number" name="stock" required placeholder="100">
            </div>
            <div class="form-group">
                <label>Palabras clave (separadas por comas):</label>
                <input type="text" name="keywords" placeholder="taper,tupper,contenedor">
            </div>
            <button type="submit" class="btn">Agregar Producto</button>
        </form>
        
        <h2>📦 Productos Actuales</h2>
        <table>
            <thead>
                <tr>
                    <th>Nombre</th>
                    <th>Precio</th>
                    <th>Stock</th>
                    <th>Keywords</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
                {% for product in products %}
                <tr>
                    <td>{{ product.name }}</td>
                    <td>{{ product.price }} bs</td>
                    <td>{{ product.stock }}</td>
                    <td>{{ product.keywords }}</td>
                    <td>{{ 'Activo' if product.active else 'Inactivo' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <h2>🔥 Leads Calientes</h2>
        <div id="leads">
            <p>Cargando leads...</p>
        </div>
    </div>
    
    <script>
        async function loadLeads() {
            try {
                const response = await fetch('/admin/leads');
                const data = await response.json();
                
                const leadsDiv = document.getElementById('leads');
                
                if (data.leads.length === 0) {
                    leadsDiv.innerHTML = '<p>No hay leads pendientes</p>';
                    return;
                }
                
                leadsDiv.innerHTML = data.leads.map(lead => `
                    <div style="background: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #ffc107;">
                        <strong>📱 ${lead.phone}</strong><br>
                        🛍️ Productos: ${lead.products}<br>
                        📝 ${lead.conversation.substring(0, 100)}...<br>
                        ⏰ ${new Date(lead.created_at).toLocaleString('es-ES')}
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Error loading leads:', error);
            }
        }
        
        loadLeads();
        setInterval(loadLeads, 10000); // Actualizar cada 10 segundos
    </script>
</body>
</html>
'''

@app.route('/admin')
def admin_panel():
    products = db.get_all_products(active_only=False)
    return render_template_string(ADMIN_TEMPLATE, 
                                products=products, 
                                business_name=BUSINESS_CONFIG['name'])

@app.route('/admin/add', methods=['POST'])
def add_product():
    try:
        name = request.form['name']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        keywords = request.form.get('keywords', '')
        
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, price, stock, keywords) VALUES (?, ?, ?, ?)",
            (name, price, stock, keywords)
        )
        conn.commit()
        conn.close()
        
        products = db.get_all_products(active_only=False)
        return render_template_string(ADMIN_TEMPLATE, 
                                    products=products, 
                                    business_name=BUSINESS_CONFIG['name'],
                                    message=f"✅ Producto '{name}' agregado",
                                    success=True)
        
    except Exception as e:
        products = db.get_all_products(active_only=False)
        return render_template_string(ADMIN_TEMPLATE, 
                                    products=products, 
                                    business_name=BUSINESS_CONFIG['name'],
                                    message=f"❌ Error: {str(e)}",
                                    success=False)

@app.route('/admin/leads')
def get_leads():
    """API para obtener leads calientes"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT phone, products_interested, conversation_summary, created_at FROM hot_leads WHERE contacted = FALSE ORDER BY created_at DESC"
    )
    leads = cursor.fetchall()
    conn.close()
    
    return jsonify({
        "leads": [
            {
                "phone": lead[0],
                "products": lead[1],
                "conversation": lead[2],
                "created_at": lead[3]
            } for lead in leads
        ]
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "status": "Bot Objetivo funcionando ✅",
        "business": BUSINESS_CONFIG['name'],
        "version": "4.0 - Súper Directo",
        "products_count": len(db.get_all_products()),
        "groq_status": "connected" if client else "fallback mode",
        "features": [
            "✅ Respuestas súper directas",
            "✅ Detección automática de teléfonos", 
            "✅ Notificaciones de leads calientes",
            "✅ Panel admin simple",
            "✅ Orientado 100% a ventas"
        ]
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": f"🎯 {BUSINESS_CONFIG['name']} - Bot Súper Directo v4.0",
        "status": "online",
        "conversacion_ejemplo": {
            "cliente": "tiene taper?",
            "bot": "Sí",
            "cliente": "precio?", 
            "bot": "35 bs",
            "cliente": "quiero dos",
            "bot": "Ok. Dame tu teléfono"
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting objective sales bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
