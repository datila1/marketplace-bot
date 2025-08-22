# 📘 Configuración de Facebook Messenger Bot

## 🎯 PASOS PARA CONFIGURAR TU BOT EN FACEBOOK

### **PASO 1: Crear App en Facebook Developers**

1. **Ir a Facebook Developers**
   ```
   https://developers.facebook.com/
   ```

2. **Crear Nueva Aplicación**
   - Clic en "Crear app"
   - Selecciona "Empresa" 
   - Nombre: "Mi Bot Marketplace"
   - Email: tu email
   - Clic en "Crear app"

### **PASO 2: Configurar Messenger Platform**

1. **Añadir Messenger**
   - En el dashboard, busca "Messenger"
   - Clic en "Configurar"

2. **Generar Page Access Token**
   - Ve a "Tokens de acceso"
   - Selecciona tu página de Facebook
   - Clic en "Generar token"
   - **COPIA EL TOKEN** (empieza con EAA...)

3. **Obtener App Secret**
   - Ve a "Configuración" → "Básica"
   - Busca "Clave secreta de la app"
   - Clic en "Mostrar"
   - **COPIA LA CLAVE SECRETA**

### **PASO 3: Instalar y Configurar ngrok**

1. **Descargar ngrok**
   ```
   https://ngrok.com/download
   ```
   - Descarga para Windows
   - Extrae ngrok.exe a una carpeta

2. **Crear cuenta en ngrok**
   ```
   https://dashboard.ngrok.com/signup
   ```

3. **Configurar authtoken**
   ```cmd
   ngrok authtoken TU_AUTHTOKEN_DE_NGROK
   ```

### **PASO 4: Configurar Variables de Entorno**

Edita el archivo `.env` en tu proyecto:

```env
# Reemplaza estos valores:
PAGE_ACCESS_TOKEN=EAA...tu_token_de_facebook
FACEBOOK_APP_SECRET=tu_app_secret_de_facebook
VERIFY_TOKEN=mi_token_secreto_marketplace_2024
```

### **PASO 5: Ejecutar el Bot y ngrok**

1. **Terminal 1 - Ejecutar el bot**
   ```cmd
   cd C:\Users\datila\Desktop\marketplace-bot-local
   python app.py
   ```

2. **Terminal 2 - Ejecutar ngrok**
   ```cmd
   ngrok http 5000
   ```
   
   Verás algo como:
   ```
   Forwarding    https://abc123.ngrok.io -> http://localhost:5000
   ```
   
   **COPIA LA URL HTTPS** (abc123.ngrok.io)

### **PASO 6: Configurar Webhook en Facebook**

1. **En Facebook Developers**
   - Ve a Messenger → Configuración
   - Busca "Webhooks"
   - Clic en "Configurar webhooks"

2. **Configurar Webhook**
   ```
   URL de callback: https://TU_URL_NGROK.ngrok.io/webhook
   Token de verificación: mi_token_secreto_marketplace_2024
   ```

3. **Suscribirse a Eventos**
   - Marca: `messages`
   - Marca: `messaging_postbacks`
   - Clic en "Verificar y guardar"

4. **Suscribir la Página**
   - En "Webhooks", selecciona tu página
   - Clic en "Suscribir"

### **PASO 7: Probar el Bot**

1. **Ir a tu página de Facebook**
2. **Enviar mensaje desde Messenger**
3. **Probar conversación**:
   ```
   Tú: "tappers"
   Bot: "Sí"
   
   Tú: "precio"
   Bot: "35 bs"
   
   Tú: "dos"
   Bot: "Ok. Deme su teléfono"
   ```

## 🔧 CONFIGURACIÓN ADICIONAL

### **Modo de Desarrollo vs Producción**

**Desarrollo:**
- Usa ngrok para exponer localhost
- Solo tú puedes probar el bot

**Producción:**
- Sube el bot a un servidor con HTTPS
- Solicita revisión de la app en Facebook
- Todos pueden usar el bot

### **Permisos Necesarios**

En Facebook Developers, solicita estos permisos:
- `pages_messaging`
- `pages_show_list`

### **Comandos Útiles**

```cmd
# Reiniciar el bot
Ctrl+C (para parar)
python app.py

# Ver logs en tiempo real
tail -f bot.log

# Verificar que el webhook funciona
curl -X GET "https://TU_URL_NGROK.ngrok.io/webhook?hub.verify_token=mi_token_secreto_marketplace_2024&hub.challenge=123"
```

## ⚠️ SOLUCIÓN DE PROBLEMAS

### **Error: Webhook no se verifica**
- Verifica que ngrok esté corriendo
- Verifica que la URL sea HTTPS
- Verifica que el VERIFY_TOKEN coincida

### **Error: Bot no responde**
- Revisa los logs: `tail -f bot.log`
- Verifica el PAGE_ACCESS_TOKEN
- Verifica que la página esté suscrita al webhook

### **Error: ngrok desconectado**
- Reinstala ngrok
- Verifica tu authtoken
- Prueba con: `ngrok http 5000 --log=stdout`

## 📱 TESTING

Una vez configurado, puedes probar:

1. **Test local**: http://localhost:5000/test
2. **Test Facebook**: Messenger de tu página
3. **Panel admin**: http://localhost:5000/admin

## 🚀 PRÓXIMOS PASOS

1. Configurar respuestas automáticas más avanzadas
2. Integrar con WhatsApp Business
3. Añadir catálogo de productos
4. Configurar pagos automáticos

---

**¿Necesitas ayuda?** Revisa los logs o contacta para soporte técnico.