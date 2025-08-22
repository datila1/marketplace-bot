from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os
import logging
import json
import re
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Base de datos SQLite
DATABASE = 'marketplace_bot.db'

def init_db():
    """Inicializar la base de datos SQLite"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            lead_captured BOOLEAN DEFAULT FALSE,
            phone_number TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            phone_number TEXT NOT NULL,
            products_interested TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            key_name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            keywords TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertar productos iniciales si la tabla está vacía
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        initial_products = [
            ('Tappers', 'tappers', 35, 50, 'tapper,tappers,recipiente,contenedor,tupper', 'Recipientes herméticos de alta calidad'),
            ('Vasos', 'vasos', 12, 30, 'vaso,vasos,copa,copas', 'Vasos resistentes para uso diario'),
            ('Platos', 'platos', 20, 25, 'plato,platos,plato hondo,plato llano', 'Platos duraderos para toda la familia')
        ]
        
        cursor.executemany('''
            INSERT INTO products (name, key_name, price, stock, keywords, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', initial_products)
        
        logging.info("Productos iniciales agregados a la base de datos")
    
    conn.commit()
    conn.close()
    logging.info("Base de datos inicializada correctamente")

def save_conversation(user_id, message, bot_response, phone_number=None):
    """Guardar conversación en la base de datos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    lead_captured = phone_number is not None
    
    cursor.execute('''
        INSERT INTO conversations (user_id, message, bot_response, lead_captured, phone_number)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, message, bot_response, lead_captured, phone_number))
    
    conn.commit()
    conn.close()
    
    logging.info(f"Conversación guardada - User: {user_id}, Message: {message}, Response: {bot_response}")

def get_bot_message_count(user_id):
    """Contar cuántos mensajes ha enviado el bot a este usuario"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM conversations 
        WHERE user_id = ? AND bot_response != ''
    ''', (user_id,))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

def apply_response_delay(user_id):
    """Aplicar retraso de 4 segundos a partir del 3er mensaje del bot"""
    message_count = get_bot_message_count(user_id)
    
    # A partir del mensaje #3 del bot, agregar retraso
    if message_count >= 2:  # >= 2 porque estamos por enviar el 3er mensaje
        logging.info(f"🕐 Aplicando retraso de 4s (mensaje #{message_count + 1} para usuario {user_id})")
        time.sleep(4)

def send_whatsapp_notification(lead_info):
    """Enviar notificación a WhatsApp cuando se capture un lead"""
    owner_phone = "+59178056048"  # Tu número de WhatsApp
    
    message = f"🔔 NUEVO LEAD CAPTURADO!\n\n📱 Cliente: {lead_info['phone']}\n🛍️ Productos: {', '.join(lead_info['products'])}\n⏰ Hora: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n💬 Contactar al cliente ahora!"
    
    # Opción 1: WhatsApp Business API gratuito (ultramsg.com)
    try:
        ultramsg_token = os.getenv('ULTRAMSG_TOKEN', '')
        ultramsg_instance = os.getenv('ULTRAMSG_INSTANCE', '')
        
        if ultramsg_token and ultramsg_instance:
            url = f"https://api.ultramsg.com/{ultramsg_instance}/messages/chat"
            payload = {
                "token": ultramsg_token,
                "to": owner_phone.replace('+', ''),
                "body": message
            }
            
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                logging.info(f"✅ Notificación WhatsApp enviada exitosamente")
                return True
            else:
                logging.warning(f"Error enviando WhatsApp via UltraMsg: {response.status_code}")
    except Exception as e:
        logging.error(f"Error enviando notificación WhatsApp: {e}")
    
    # Opción 2: CallMeBot (backup)
    try:
        callmebot_key = os.getenv('CALLMEBOT_API_KEY', '')
        if callmebot_key:
            callmebot_url = f"https://api.callmebot.com/whatsapp.php"
            params = {
                'phone': owner_phone.replace('+', ''),
                'text': message,
                'apikey': callmebot_key
            }
            
            response = requests.get(callmebot_url, params=params)
            if response.status_code == 200:
                logging.info(f"✅ Notificación WhatsApp enviada via CallMeBot")
                return True
    except Exception as e:
        logging.error(f"Error con CallMeBot: {e}")
    
    # Opción 3: Log detallado para monitoreo manual
    logging.info(f"🔔🔔🔔 LEAD CAPTURADO - CONTACTAR CLIENTE: {lead_info['phone']} - PRODUCTOS: {', '.join(lead_info['products'])} 🔔🔔🔔")
    
    # Opción 4: Escribir a archivo para monitoreo
    try:
        with open('leads_urgentes.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%H:%M %d/%m/%Y')} - CLIENTE: {lead_info['phone']} - PRODUCTOS: {', '.join(lead_info['products'])}\n")
    except Exception as e:
        logging.error(f"Error escribiendo archivo leads: {e}")
    
    return False

def save_lead(user_id, phone_number, products_interested):
    """Guardar lead en la base de datos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO leads (user_id, phone_number, products_interested)
            VALUES (?, ?, ?)
        ''', (user_id, phone_number, json.dumps(products_interested)))
        
        conn.commit()
        logging.info(f"Lead capturado - User: {user_id}, Phone: {phone_number}, Products: {products_interested}")
        
        # Enviar notificación a WhatsApp del dueño
        lead_info = {
            'phone': phone_number,
            'products': products_interested,
            'user_id': user_id
        }
        send_whatsapp_notification(lead_info)
        
    except Exception as e:
        logging.error(f"Error guardando lead: {e}")
    finally:
        conn.close()

def get_active_products():
    """Obtener productos activos y en stock desde la base de datos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT key_name, name, price, stock, keywords, description 
        FROM products 
        WHERE active = TRUE AND stock > 0
        ORDER BY name
    ''')
    
    products = {}
    for row in cursor.fetchall():
        key_name, name, price, stock, keywords, description = row
        products[key_name] = {
            'name': name,
            'price': price,
            'stock': stock,
            'keywords': keywords.split(','),
            'description': description
        }
    
    conn.close()
    return products

def detect_product(message):
    """Detectar qué producto menciona el usuario (usando base de datos)"""
    message_lower = message.lower()
    products = get_active_products()
    
    for product_key, product_info in products.items():
        for keyword in product_info['keywords']:
            if keyword.strip().lower() in message_lower:
                return product_key, product_info
    
    return None, None

def detect_phone_number(message):
    """Detectar número de teléfono en el mensaje"""
    # Patrones para detectar teléfonos bolivianos
    patterns = [
        r'\b(\d{8})\b',  # 8 dígitos seguidos
        r'\b(\d{4}[-\s]?\d{4})\b',  # 4-4 dígitos con guión o espacio
        r'\b7[0-9]{7}\b',  # Celulares que empiezan con 7
        r'\b6[0-9]{7}\b',  # Celulares que empiezan con 6
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1).replace('-', '').replace(' ', '')
    
    return None

def detect_quantity(message):
    """Detectar cantidad en el mensaje"""
    message_lower = message.lower()
    
    # Números escritos
    word_numbers = {
        'uno': 1, 'una': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
        'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10
    }
    
    for word, number in word_numbers.items():
        if word in message_lower:
            return number
    
    # Números en dígitos
    number_match = re.search(r'\b(\d+)\b', message)
    if number_match:
        return int(number_match.group(1))
    
    return None

def is_quantity_inquiry(message):
    """Detectar si es una consulta de cantidad (no una compra definitiva)"""
    message_lower = message.lower()
    
    # Palabras que indican consulta/pregunta
    inquiry_keywords = [
        'no me hace precio', 'me hace precio', 'precio', 'cuanto', 'cuánto',
        'en cuanto', 'sale', 'vale', 'cuesta', '?'
    ]
    
    return any(keyword in message_lower for keyword in inquiry_keywords)

def send_facebook_message(recipient_id, message_text):
    """Enviar mensaje de respuesta a Facebook Messenger"""
    page_access_token = os.getenv('PAGE_ACCESS_TOKEN')
    
    if not page_access_token or page_access_token == 'PEGA_AQUI_TU_PAGE_ACCESS_TOKEN':
        logging.warning("PAGE_ACCESS_TOKEN no configurado. No se puede enviar mensaje a Facebook.")
        return False
    
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={page_access_token}"
    
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            logging.info(f"Mensaje enviado a Facebook: {message_text}")
            return True
        else:
            logging.error(f"Error enviando mensaje a Facebook: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Excepción enviando mensaje a Facebook: {e}")
        return False

def detect_gender_from_conversations(user_id):
    """Detectar género basado en nombres mencionados en conversaciones"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Buscar mensajes que podrían contener nombres
    cursor.execute('''
        SELECT message FROM conversations 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 20
    ''', (user_id,))
    
    messages = cursor.fetchall()
    conn.close()
    
    # Base de datos de nombres femeninos comunes en Bolivia
    female_names = [
        'maria', 'ana', 'rosa', 'carmen', 'elena', 'patricia', 'laura', 'sofia', 'daniela',
        'andrea', 'veronica', 'monica', 'gabriela', 'alejandra', 'claudia', 'silvia',
        'martha', 'gloria', 'teresa', 'beatriz', 'lucia', 'cristina', 'diana', 'rocio',
        'paola', 'carla', 'sandra', 'janet', 'yolanda', 'norma', 'lidia', 'susana',
        'marcela', 'karen', 'fernanda', 'vanessa', 'jessica', 'leslie', 'nicole',
        'valeria', 'natalia', 'carolina', 'adriana', 'karina', 'viviana', 'lorena'
    ]
    
    # Base de datos de nombres masculinos comunes en Bolivia
    male_names = [
        'juan', 'carlos', 'luis', 'jose', 'antonio', 'francisco', 'miguel', 'pedro',
        'jorge', 'roberto', 'ricardo', 'fernando', 'daniel', 'david', 'mario',
        'sergio', 'alejandro', 'manuel', 'raul', 'eduardo', 'pablo', 'oscar',
        'rafael', 'marco', 'hugo', 'ivan', 'cesar', 'gabriel', 'javier', 'martin',
        'diego', 'andres', 'cristian', 'walter', 'erick', 'ronald', 'fabian',
        'adrian', 'orlando', 'nelson', 'wilson', 'freddy', 'ramiro', 'aldo'
    ]
    
    # Analizar mensajes buscando nombres
    all_text = ' '.join([msg[0].lower() for msg in messages])
    
    # Contar nombres femeninos y masculinos encontrados
    female_count = sum(1 for name in female_names if name in all_text)
    male_count = sum(1 for name in male_names if name in all_text)
    
    # Decidir género basado en nombres encontrados
    if female_count > male_count:
        return 'female'
    elif male_count > female_count:
        return 'male'
    else:
        return 'neutral'  # No se pudo determinar

def get_gendered_greeting(user_id):
    """Obtener saludo con género correcto"""
    gender = detect_gender_from_conversations(user_id)
    
    if gender == 'female':
        return 'estimada'
    elif gender == 'male':
        return 'estimado'
    else:
        return 'estimado(a)'  # Default si no se puede determinar

def calculate_discount_and_total(quantity, unit_price):
    """Calcular descuento y total basado en cantidad"""
    if quantity <= 2:
        discount_percent = 0
        discount_amount = 0
    elif quantity == 3:
        # Precio especial: 3 tapper = 95bs
        total_normal = quantity * unit_price  # 105bs
        discount_amount = total_normal - 95   # 10bs
        discount_percent = 10
    elif quantity in [4, 5]:
        # Mantener el mismo descuento proporcional
        discount_amount = 15
        discount_percent = 10
    elif quantity == 6:
        discount_percent = 8
        discount_amount = (quantity * unit_price) * (discount_percent / 100)
    else:  # 7 o más (no especificado en el nuevo flujo)
        discount_percent = 10
        discount_amount = (quantity * unit_price) * (discount_percent / 100)
    
    subtotal = quantity * unit_price
    total = subtotal - discount_amount
    
    return {
        'discount_percent': discount_percent,
        'discount_amount': round(discount_amount),
        'subtotal': subtotal,
        'total': round(total),
        'has_discount': discount_amount > 0
    }

def get_bot_response(user_id, message):
    """Generar respuesta del bot basada en el mensaje del usuario"""
    
    # Aplicar retraso a partir del 3er mensaje del bot
    apply_response_delay(user_id)
    
    message_lower = message.lower().strip()
    
    # Obtener conversaciones previas del usuario
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT message, bot_response FROM conversations 
        WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5
    ''', (user_id,))
    previous_conversations = cursor.fetchall()
    conn.close()
    
    # Detectar número de teléfono
    phone = detect_phone_number(message)
    if phone:
        # Guardar como lead
        products_mentioned = []
        for conv_msg, _ in previous_conversations:
            product_key, _ = detect_product(conv_msg)
            if product_key and product_key not in products_mentioned:
                products_mentioned.append(product_key)
        
        save_lead(user_id, phone, products_mentioned)
        return "te escribo", phone
    
    # Analizar contexto conversacional
    last_bot_response = previous_conversations[0][1] if previous_conversations else ""
    
    # Detectar negociación/descuento (con cantidad específica)
    negotiation_keywords = [
        'nada menos', 'descuento', 'rebaja', 'barato', 'más barato', 'mas barato',
        'promocion', 'promoción', 'oferta', 'menos precio', 'precio mejor',
        'más económico', 'mas economico', 'algo menos', 'no hay descuento'
    ]
    
    # Detectar si menciona cantidad en la negociación (ej: "nada menos? quiero 4")
    quantity_in_negotiation = detect_quantity(message)
    
    if any(keyword in message_lower for keyword in negotiation_keywords):
        # Buscar el último producto mencionado
        last_product = None
        for conv_msg, _ in previous_conversations:
            product_key, product_info = detect_product(conv_msg)
            if product_key:
                last_product = product_info
                break
        
        if last_product:
            # Si mencionó cantidad específica en la negociación
            if quantity_in_negotiation:
                calc = calculate_discount_and_total(quantity_in_negotiation, last_product['price'])
                gendered_greeting = get_gendered_greeting(user_id)
                if calc['has_discount']:
                    return f"Nada menos {gendered_greeting}, pero si lleva {quantity_in_negotiation} le hago {calc['discount_percent']}% descuento = {calc['total']}bs con envío gratis hasta el cuarto anillo", None
                else:
                    return f"Nada menos {gendered_greeting}, {quantity_in_negotiation} unidades = {calc['total']}bs con envío gratis hasta el cuarto anillo", None
            else:
                # Ofrecer la mejor opción (3 unidades con 5% descuento)
                calc = calculate_discount_and_total(3, last_product['price'])
                gendered_greeting = get_gendered_greeting(user_id)
                return f"Nada menos {gendered_greeting}, pero si lleva 3 le hago descuento de 10bs = 95bs", None
        else:
            gendered_greeting = get_gendered_greeting(user_id)
            return f"Nada menos {gendered_greeting}, los descuentos se aplican a partir de:\n3 tapper a 95bs = descuento de 10bs", None
    
    # Detectar preguntas sobre delivery/entrega
    delivery_keywords = ['entrega', 'delivery', 'domicilio', 'entregan', 'envio', 'envío', 'traen']
    if any(keyword in message_lower for keyword in delivery_keywords):
        return "si, pero la entrega no incluye el precio, usted tendria que pagar por el delivery, o caso contrario podria recogerlo del almacen", None
    
    # Detectar confirmación sobre recojo
    pickup_keywords = ['recoger', 'pasar a recoger', 'puedo pasar', 'voy a recoger', 'recojo']
    if any(keyword in message_lower for keyword in pickup_keywords):
        return "ok, mandeme su numero para que le mande ubicacion", None
    
    # Detectar solicitud de teléfono del vendedor
    phone_request_keywords = ['su telefono', 'tu telefono', 'mandeme su telefono', 'dame tu numero']
    if any(keyword in message_lower for keyword in phone_request_keywords):
        return "mejor mandeme asi yo puedo mandarle el mensajito, y coordinamos por whatsap", None
    
    # Detectar confirmación después de precio (pero solo si no menciona cantidad)
    confirmation_keywords = ['ok', 'está bien', 'esta bien', 'bueno', 'dale', 'sale', 'si me parece', 'me parece bien']
    if any(keyword in message_lower for keyword in confirmation_keywords):
        # Verificar contexto de la conversación anterior
        if 'descuento' in last_bot_response or 'bs' in last_bot_response:
            if not detect_quantity(message):
                return "va querer 1 o 3?", None
        elif 'envio' in last_bot_response or 'delivery' in last_bot_response:
            return "esta bien, mandeme su telefono", None
        elif not detect_quantity(message):
            return "¿Cuántos quiere?", None
    
    # Detectar agradecimientos
    thanks_keywords = ['gracias', 'graciad', 'grax', 'thank']
    if any(keyword in message_lower for keyword in thanks_keywords):
        return "De nada! ¿Le interesa algún producto?", None
    
    # Detectar despedidas
    goodbye_keywords = ['chau', 'adiós', 'adios', 'hasta luego', 'nos vemos', 'bye']
    if any(keyword in message_lower for keyword in goodbye_keywords):
        return "¡Hasta luego! Cualquier cosa me escribe", None
    
    # Detectar cantidad PRIMERO (para preguntas como "y 5 unidades en cuanto?")
    quantity = detect_quantity(message)
    if quantity:
        # Buscar último producto mencionado para calcular precio
        last_product = None
        for conv_msg, _ in previous_conversations:
            product_key, product_info = detect_product(conv_msg)
            if product_key:
                last_product = product_info
                break
        
        if last_product:
            calc = calculate_discount_and_total(quantity, last_product['price'])
            
            if quantity == 1:
                return f"esta bien, si gusta puedo hacerle el envio o puede pasar a recogerlo", None
            elif calc['has_discount']:
                # Verificar si es una consulta o compra definitiva
                if is_quantity_inquiry(message):
                    return f"{quantity} tapper en {calc['total']}bs con descuento de {calc['discount_amount']}bs", None
                else:
                    return f"ok si quiere {quantity} te hago un descuento de {calc['discount_amount']}bs, {quantity} tapper en {calc['total']}bs", None
            else:
                # Sin descuento (2 unidades) - mencionar descuento disponible
                if is_quantity_inquiry(message):
                    return f"Ok, {quantity} tapper en {calc['total']}bs con envío gratis hasta el cuarto anillo, se aplica descuento apartir de 3 unidades", None
                else:
                    return f"Ok, {quantity} tapper en {calc['total']}bs con envío gratis hasta el cuarto anillo, se aplica descuento apartir de 3 unidades. Deme su teléfono", None
        else:
            return "Ok. Deme su teléfono para coordinar", None
    
    # Detectar pregunta de precio (ahora va después de cantidad)
    price_keywords = [
        'precio', 'cuesta', 'vale', 'cuanto', 'cuánto', 'costa', 'costo',
        'están', 'estan', 'cuanto sale', 'cuánto sale', 'a cuanto', 'a cuánto',
        'que precio', 'qué precio', 'cuanto vale', 'cuánto vale', 'que cuesta',
        'qué cuesta', 'cuanto cuesta', 'cuánto cuesta'
    ]
    if any(keyword in message_lower for keyword in price_keywords):
        # Primero verificar si menciona un producto específico en el mismo mensaje
        product_key, product_info = detect_product(message)
        if product_key:
            return f"{product_info['price']} bs", None
        
        # Si no, buscar el último producto mencionado en la conversación
        for conv_msg, _ in previous_conversations:
            product_key, product_info = detect_product(conv_msg)
            if product_key:
                return f"{product_info['price']} bs", None
        
        # Si no hay producto específico, mostrar todos los precios disponibles
        products = get_active_products()
        if products:
            price_list = ", ".join([f"{info['name']}: {info['price']}bs" for info in products.values()])
            return price_list, None
        else:
            return "No tengo productos disponibles en este momento", None
    
    # Detectar producto (respuesta directa y comercial)
    product_key, product_info = detect_product(message)
    if product_key:
        return f"Sí, tenemos a {product_info['price']}bs", None
    
    # Saludos directos
    if any(word in message_lower for word in ['hola', 'buenos', 'buenas', 'saludos']):
        return "Hola, ¿en qué te puedo ayudar?", None
    
    # Detectar interés general
    interest_keywords = ['busco', 'necesito', 'quiero comprar', 'me interesa', 'quisiera']
    if any(keyword in message_lower for keyword in interest_keywords):
        products = get_active_products()
        if products:
            product_list = ", ".join([f"{info['name']} ({info['price']}bs)" for info in products.values()])
            return f"Perfecto! Tengo {product_list}. ¿Qué le interesa?", None
        else:
            return "Disculpe, no tengo productos disponibles en este momento", None
    
    # Respuesta por defecto con productos dinámicos
    products = get_active_products()
    if products:
        product_list = ", ".join([f"{info['name']} ({info['price']}bs)" for info in products.values()])
        return f"¿En qué le puedo ayudar? Tengo {product_list} de excelente calidad", None
    else:
        return "Hola, estoy actualizando mi inventario. Pronto tendré productos disponibles", None

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Webhook para Facebook Messenger"""
    
    if request.method == 'GET':
        # Verificación del webhook
        verify_token = os.getenv('VERIFY_TOKEN', 'mi_token_secreto')
        
        if request.args.get('hub.verify_token') == verify_token:
            logging.info("Webhook verificado correctamente")
            return request.args.get('hub.challenge')
        else:
            logging.error("Token de verificación incorrecto")
            return 'Error de verificación', 403
    
    elif request.method == 'POST':
        # Procesar mensaje entrante
        data = request.get_json()
        logging.info(f"Mensaje recibido: {data}")
        
        if 'entry' in data:
            for entry in data['entry']:
                if 'messaging' in entry:
                    for messaging_event in entry['messaging']:
                        if 'message' in messaging_event:
                            sender_id = messaging_event['sender']['id']
                            
                            if 'text' in messaging_event['message']:
                                message_text = messaging_event['message']['text']
                                
                                # Generar respuesta
                                bot_response, phone = get_bot_response(sender_id, message_text)
                                
                                # Guardar conversación
                                save_conversation(sender_id, message_text, bot_response, phone)
                                
                                # Enviar respuesta a Facebook
                                send_facebook_message(sender_id, bot_response)
                                
                                logging.info(f"Respuesta procesada: {bot_response}")
                                
                                return jsonify({'status': 'success', 'response': bot_response})
        
        return jsonify({'status': 'success'})

@app.route('/test', methods=['GET', 'POST'])
def test():
    """Endpoint para probar el bot localmente"""
    if request.method == 'GET':
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bot Test</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
                .chat-container { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; margin-bottom: 10px; }
                .user-message { text-align: right; margin: 5px 0; }
                .bot-message { text-align: left; margin: 5px 0; color: blue; }
                input[type="text"] { width: 80%; padding: 5px; }
                button { padding: 5px 15px; }
            </style>
        </head>
        <body>
            <h1>Test del Bot de Marketplace</h1>
            <div class="chat-container" id="chatContainer"></div>
            <input type="text" id="messageInput" placeholder="Escribe tu mensaje..." onkeypress="handleEnter(event)">
            <button onclick="sendMessage()">Enviar</button>
            
            <script>
                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    // Mostrar mensaje del usuario
                    addMessage('user', message);
                    input.value = '';
                    
                    // Enviar al bot
                    fetch('/test', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: message, user_id: 'test_user'})
                    })
                    .then(response => response.json())
                    .then(data => {
                        addMessage('bot', data.response);
                    });
                }
                
                function addMessage(type, text) {
                    const container = document.getElementById('chatContainer');
                    const div = document.createElement('div');
                    div.className = type + '-message';
                    div.textContent = (type === 'user' ? 'Tú: ' : 'Bot: ') + text;
                    container.appendChild(div);
                    container.scrollTop = container.scrollHeight;
                }
                
                function handleEnter(event) {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }
            </script>
        </body>
        </html>
        ''')
    
    elif request.method == 'POST':
        data = request.get_json()
        message = data.get('message', '')
        user_id = data.get('user_id', 'test_user')
        
        bot_response, phone = get_bot_response(user_id, message)
        save_conversation(user_id, message, bot_response, phone)
        
        return jsonify({'response': bot_response})

@app.route('/admin')
def admin():
    """Panel de administración simple"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Obtener estadísticas
    cursor.execute('SELECT COUNT(*) FROM conversations')
    total_conversations = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM leads')
    total_leads = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM conversations')
    unique_users = cursor.fetchone()[0]
    
    # Últimas conversaciones
    cursor.execute('''
        SELECT user_id, message, bot_response, timestamp 
        FROM conversations 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''')
    recent_conversations = cursor.fetchall()
    
    # Leads capturados
    cursor.execute('''
        SELECT user_id, phone_number, products_interested, timestamp 
        FROM leads 
        ORDER BY timestamp DESC
    ''')
    leads = cursor.fetchall()
    
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Panel de Administración</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .stats { display: flex; gap: 20px; margin-bottom: 30px; }
            .stat-box { border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }
            .stat-number { font-size: 2em; font-weight: bold; color: #2196F3; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .section { margin-bottom: 40px; }
            h1, h2 { color: #333; }
        </style>
    </head>
    <body>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
            <h1>Panel de Administración - Marketplace Bot</h1>
            <a href="/products" style="padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px;">📦 Gestionar Productos</a>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{{ total_conversations }}</div>
                <div>Total Conversaciones</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ total_leads }}</div>
                <div>Leads Capturados</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ unique_users }}</div>
                <div>Usuarios Únicos</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Leads Capturados</h2>
            <table>
                <tr>
                    <th>Usuario ID</th>
                    <th>Teléfono</th>
                    <th>Productos de Interés</th>
                    <th>Fecha</th>
                </tr>
                {% for lead in leads %}
                <tr>
                    <td>{{ lead[0] }}</td>
                    <td>{{ lead[1] }}</td>
                    <td>{{ lead[2] }}</td>
                    <td>{{ lead[3] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="section">
            <h2>Últimas Conversaciones</h2>
            <table>
                <tr>
                    <th>Usuario ID</th>
                    <th>Mensaje</th>
                    <th>Respuesta Bot</th>
                    <th>Fecha</th>
                </tr>
                {% for conv in recent_conversations %}
                <tr>
                    <td>{{ conv[0] }}</td>
                    <td>{{ conv[1] }}</td>
                    <td>{{ conv[2] }}</td>
                    <td>{{ conv[3] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    ''', 
    total_conversations=total_conversations, 
    total_leads=total_leads, 
    unique_users=unique_users,
    leads=leads,
    recent_conversations=recent_conversations
    )

@app.route('/analytics')
def analytics():
    """Endpoint de analytics simple"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Productos más consultados
    cursor.execute('''
        SELECT bot_response, COUNT(*) as count 
        FROM conversations 
        WHERE bot_response LIKE '%bs%'
        GROUP BY bot_response
        ORDER BY count DESC
    ''')
    price_queries = cursor.fetchall()
    
    # Conversaciones por día
    cursor.execute('''
        SELECT DATE(timestamp) as date, COUNT(*) as count 
        FROM conversations 
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 7
    ''')
    daily_stats = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'price_queries': price_queries,
        'daily_conversations': daily_stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test_response', methods=['POST'])
def test_response():
    """Endpoint para probar respuestas del bot"""
    data = request.get_json()
    user_id = data.get('user_id', 'test_user')
    message = data.get('message', '')
    
    # Guardar conversación y obtener respuesta
    save_conversation(user_id, message, '')
    response, phone = get_bot_response(user_id, message)
    save_conversation(user_id, message, response)
    
    return jsonify({
        'user_id': user_id,
        'message': message,
        'response': response,
        'phone': phone
    })

@app.route('/products')
def products():
    """Panel de gestión de productos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, key_name, price, stock, keywords, description, active 
        FROM products 
        ORDER BY name
    ''')
    all_products = cursor.fetchall()
    
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gestión de Productos - Marketplace Bot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
            .btn { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; }
            .btn:hover { background: #0056b3; }
            .btn-success { background: #28a745; }
            .btn-danger { background: #dc3545; }
            .btn-warning { background: #ffc107; color: black; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f8f9fa; }
            .status-active { color: #28a745; font-weight: bold; }
            .status-inactive { color: #dc3545; font-weight: bold; }
            .stock-high { color: #28a745; }
            .stock-medium { color: #ffc107; }
            .stock-low { color: #dc3545; }
            .form-container { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
            .form-row { display: flex; gap: 15px; margin-bottom: 15px; }
            .form-group { flex: 1; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            textarea { height: 60px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📦 Gestión de Productos</h1>
            <div>
                <a href="/admin" class="btn">← Panel Admin</a>
                <button onclick="toggleForm()" class="btn btn-success">+ Agregar Producto</button>
            </div>
        </div>

        <div id="productForm" class="form-container" style="display: none;">
            <h3>Agregar/Editar Producto</h3>
            <form id="productFormElement">
                <input type="hidden" id="productId" name="id">
                <div class="form-row">
                    <div class="form-group">
                        <label>Nombre del Producto:</label>
                        <input type="text" id="productName" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>Clave (sin espacios):</label>
                        <input type="text" id="productKey" name="key_name" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Precio (Bs):</label>
                        <input type="number" id="productPrice" name="price" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Stock:</label>
                        <input type="number" id="productStock" name="stock" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Palabras Clave (separadas por comas):</label>
                        <div style="display: flex; gap: 5px;">
                            <input type="text" id="productKeywords" name="keywords" required style="flex: 1;">
                            <button type="button" onclick="generateKeywords()" class="btn" style="background: #17a2b8; color: white; white-space: nowrap;">💡 Sugerir</button>
                        </div>
                        <small style="color: #666; margin-top: 5px; display: block;">Palabras que los clientes podrían usar para buscar este producto</small>
                    </div>
                    <div class="form-group">
                        <label>Estado:</label>
                        <select id="productActive" name="active">
                            <option value="1">Activo</option>
                            <option value="0">Inactivo</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Descripción:</label>
                    <textarea id="productDescription" name="description"></textarea>
                </div>
                <div class="form-row">
                    <button type="submit" class="btn btn-success">Guardar Producto</button>
                    <button type="button" onclick="clearForm()" class="btn">Cancelar</button>
                </div>
            </form>
        </div>

        <table>
            <tr>
                <th>Nombre</th>
                <th>Clave</th>
                <th>Precio</th>
                <th>Stock</th>
                <th>Estado</th>
                <th>Palabras Clave</th>
                <th>Acciones</th>
            </tr>
            {% for product in products %}
            <tr>
                <td>{{ product[1] }}</td>
                <td><code>{{ product[2] }}</code></td>
                <td>{{ product[3] }} Bs</td>
                <td class="{% if product[4] > 20 %}stock-high{% elif product[4] > 5 %}stock-medium{% else %}stock-low{% endif %}">
                    {{ product[4] }} unidades
                </td>
                <td class="{% if product[7] %}status-active{% else %}status-inactive{% endif %}">
                    {{ 'Activo' if product[7] else 'Inactivo' }}
                </td>
                <td>{{ product[5] }}</td>
                <td>
                    <button onclick="editProduct({{ product[0] }}, '{{ product[1] }}', '{{ product[2] }}', {{ product[3] }}, {{ product[4] }}, '{{ product[5] }}', '{{ product[6] or '' }}', {{ product[7] }})" class="btn btn-warning">Editar</button>
                    <button onclick="deleteProduct({{ product[0] }})" class="btn btn-danger">Eliminar</button>
                </td>
            </tr>
            {% endfor %}
        </table>

        <script>
            function toggleForm() {
                const form = document.getElementById('productForm');
                form.style.display = form.style.display === 'none' ? 'block' : 'none';
            }

            function clearForm() {
                document.getElementById('productFormElement').reset();
                document.getElementById('productId').value = '';
                document.getElementById('productForm').style.display = 'none';
            }

            function editProduct(id, name, key, price, stock, keywords, description, active) {
                document.getElementById('productId').value = id;
                document.getElementById('productName').value = name;
                document.getElementById('productKey').value = key;
                document.getElementById('productPrice').value = price;
                document.getElementById('productStock').value = stock;
                document.getElementById('productKeywords').value = keywords;
                document.getElementById('productDescription').value = description;
                document.getElementById('productActive').value = active ? '1' : '0';
                document.getElementById('productForm').style.display = 'block';
            }

            function deleteProduct(id) {
                if (confirm('¿Estás seguro de eliminar este producto?')) {
                    fetch('/api/products/' + id, {method: 'DELETE'})
                    .then(() => location.reload());
                }
            }

            document.getElementById('productFormElement').addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                const method = data.id ? 'PUT' : 'POST';
                const url = data.id ? '/api/products/' + data.id : '/api/products';
                
                fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                })
                .then(() => {
                    clearForm();
                    location.reload();
                });
            });

            function generateKeywords() {
                const productName = document.getElementById('productName').value.toLowerCase();
                if (!productName) {
                    alert('Primero ingresa el nombre del producto');
                    return;
                }

                // Base de datos de palabras clave por categorías
                const keywordDatabase = {
                    // Recipientes y contenedores
                    'tapper': ['tapper', 'tappers', 'tupper', 'tuppers', 'recipiente', 'contenedor', 'hermético', 'envase', 'conservar', 'guardar'],
                    'tappers': ['tapper', 'tappers', 'tupper', 'tuppers', 'recipiente', 'contenedor', 'hermético', 'envase', 'conservar', 'guardar'],
                    'tupper': ['tapper', 'tappers', 'tupper', 'tuppers', 'recipiente', 'contenedor', 'hermético', 'envase', 'conservar', 'guardar'],
                    'recipiente': ['recipiente', 'contenedor', 'envase', 'tapper', 'tupper', 'guardar', 'conservar'],
                    'contenedor': ['contenedor', 'recipiente', 'envase', 'tapper', 'tupper', 'guardar', 'conservar'],
                    
                    // Vasos y copas
                    'vaso': ['vaso', 'vasos', 'copa', 'copas', 'taza', 'tomar', 'beber', 'líquido'],
                    'vasos': ['vaso', 'vasos', 'copa', 'copas', 'taza', 'tomar', 'beber', 'líquido'],
                    'copa': ['copa', 'copas', 'vaso', 'vasos', 'taza', 'tomar', 'beber'],
                    'copas': ['copa', 'copas', 'vaso', 'vasos', 'taza', 'tomar', 'beber'],
                    'taza': ['taza', 'tazas', 'vaso', 'copa', 'tomar', 'beber', 'café', 'té'],
                    
                    // Platos y vajilla
                    'plato': ['plato', 'platos', 'plato hondo', 'plato llano', 'vajilla', 'comer', 'comida'],
                    'platos': ['plato', 'platos', 'plato hondo', 'plato llano', 'vajilla', 'comer', 'comida'],
                    'vajilla': ['vajilla', 'plato', 'platos', 'servir', 'comer', 'comida'],
                    
                    // Cubiertos
                    'cuchara': ['cuchara', 'cucharas', 'cubierto', 'cubiertos', 'comer', 'sopa'],
                    'cucharas': ['cuchara', 'cucharas', 'cubierto', 'cubiertos', 'comer', 'sopa'],
                    'tenedor': ['tenedor', 'tenedores', 'cubierto', 'cubiertos', 'comer'],
                    'cuchillo': ['cuchillo', 'cuchillos', 'cubierto', 'cubiertos', 'cortar'],
                    
                    // Utensilios de cocina
                    'olla': ['olla', 'ollas', 'cocinar', 'hervir', 'guisar', 'sopa'],
                    'sartén': ['sartén', 'sartenes', 'freír', 'cocinar', 'plancha'],
                    'cacerola': ['cacerola', 'cacerolas', 'cocinar', 'hervir', 'guisar'],
                    
                    // Otros productos
                    'bowl': ['bowl', 'bowls', 'tazón', 'ensaladera', 'servir', 'mezclar'],
                    'bandeja': ['bandeja', 'bandejas', 'servir', 'llevar', 'transportar'],
                    'jarra': ['jarra', 'jarras', 'agua', 'jugo', 'servir', 'líquido'],
                    'botella': ['botella', 'botellas', 'agua', 'líquido', 'beber', 'tomar']
                };

                // Buscar palabras clave específicas
                let suggestedKeywords = [];
                
                // Buscar coincidencias exactas
                for (const [key, keywords] of Object.entries(keywordDatabase)) {
                    if (productName.includes(key)) {
                        suggestedKeywords = [...suggestedKeywords, ...keywords];
                    }
                }

                // Si no encontró coincidencias, generar basándose en palabras comunes
                if (suggestedKeywords.length === 0) {
                    const commonWords = ['producto', 'artículo', 'utensilio', 'cocina', 'hogar', 'casa'];
                    const productWords = productName.split(' ');
                    suggestedKeywords = [...productWords, ...commonWords];
                }

                // Agregar variaciones comunes
                suggestedKeywords.push(productName);
                suggestedKeywords.push(productName + 's'); // plural
                if (productName.endsWith('s')) {
                    suggestedKeywords.push(productName.slice(0, -1)); // singular
                }

                // Remover duplicados y limpiar
                suggestedKeywords = [...new Set(suggestedKeywords)]
                    .filter(word => word.length > 1)
                    .slice(0, 10); // Límite de 10 palabras

                // Actualizar el campo
                document.getElementById('productKeywords').value = suggestedKeywords.join(', ');
                
                // Mostrar mensaje de confirmación
                alert('✅ Se generaron ' + suggestedKeywords.length + ' palabras clave automáticamente. Puedes editarlas si necesitas.');
            }
        </script>
    </body>
    </html>
    ''', products=all_products)

@app.route('/api/products', methods=['GET', 'POST'])
def api_products():
    """API para gestionar productos"""
    if request.method == 'GET':
        products = get_active_products()
        return jsonify(products)
    
    elif request.method == 'POST':
        data = request.get_json()
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products (name, key_name, price, stock, keywords, description, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'], 
            data['key_name'], 
            float(data['price']), 
            int(data['stock']),
            data['keywords'], 
            data.get('description', ''),
            bool(int(data.get('active', 1)))
        ))
        
        conn.commit()
        conn.close()
        
        logging.info(f"Producto agregado: {data['name']}")
        return jsonify({'status': 'success'})

@app.route('/api/products/<int:product_id>', methods=['PUT', 'DELETE'])
def api_product_detail(product_id):
    """API para editar/eliminar producto específico"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.get_json()
        cursor.execute('''
            UPDATE products 
            SET name=?, key_name=?, price=?, stock=?, keywords=?, description=?, active=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            data['name'], 
            data['key_name'], 
            float(data['price']), 
            int(data['stock']),
            data['keywords'], 
            data.get('description', ''),
            bool(int(data.get('active', 1))),
            product_id
        ))
        
        conn.commit()
        conn.close()
        
        logging.info(f"Producto actualizado: ID {product_id}")
        return jsonify({'status': 'updated'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        conn.commit()
        conn.close()
        
        logging.info(f"Producto eliminado: ID {product_id}")
        return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    # Inicializar base de datos
    init_db()
    
    # Obtener configuración de variables de entorno
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    logging.info(f"🚀 Iniciando bot en puerto {port} - v1.1")
    app.run(host='0.0.0.0', port=port, debug=debug)