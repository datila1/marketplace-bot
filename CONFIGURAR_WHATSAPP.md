# 📱 Configurar Notificaciones de WhatsApp

## 🎯 OBJETIVO
Cuando un cliente dé su teléfono, el bot te enviará automáticamente un mensaje a tu WhatsApp: **+59178056048**

## ⚡ OPCIÓN 1: UltraMsg (RECOMENDADO - GRATIS)

### Pasos:
1. **Registrarse en UltraMsg:**
   - Ve a: https://ultramsg.com/
   - Crea cuenta gratuita
   - Conecta tu WhatsApp escaneando QR

2. **Obtener credenciales:**
   - Instance ID (ejemplo: `instance12345`)
   - Token (ejemplo: `abc123def456`)

3. **Configurar en .env:**
   ```env
   ULTRAMSG_TOKEN=abc123def456
   ULTRAMSG_INSTANCE=instance12345
   ```

## ⚡ OPCIÓN 2: CallMeBot (BACKUP - GRATIS)

### Pasos:
1. **Configurar CallMeBot:**
   - Envía mensaje desde tu WhatsApp: `I allow callmebot to send me messages` 
   - Al número: **+34 644 26 61 85**
   - Te responderán con tu API Key

2. **Configurar en .env:**
   ```env
   CALLMEBOT_API_KEY=tu_api_key_aqui
   ```

## 🔧 CONFIGURACIÓN ACTUAL

Tu número está configurado como: **+59178056048**

### Archivo leads_urgentes.txt
Aunque no configures APIs, el bot guardará todos los leads en:
- `leads_urgentes.txt` - Para revisar manualmente
- Logs de la terminal - Aparecerán con 🔔🔔🔔

## 🧪 PROBAR NOTIFICACIONES

1. **Reiniciar el bot** (para cargar nuevas configuraciones)
2. **Hacer prueba completa:**
   ```
   Cliente en Facebook: "tappers"
   Bot: "Sí"
   Cliente: "dos"  
   Bot: "Ok. Deme su teléfono"
   Cliente: "78123456"
   Bot: "Ok, ya te escribo al WhatsApp"
   ```
3. **Deberías recibir:** Mensaje en tu WhatsApp con datos del cliente

## 📊 MONITOREO

- **Panel admin:** http://localhost:5000/admin
- **Archivo leads:** `leads_urgentes.txt`
- **Logs terminal:** Busca 🔔🔔🔔

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Si no llegan mensajes:
1. Verifica tokens en `.env`
2. Revisa logs en terminal
3. Confirma que UltraMsg/CallMeBot estén activos
4. Usa backup: archivo `leads_urgentes.txt`

### Límites gratuitos:
- **UltraMsg:** 1000 mensajes/mes gratis
- **CallMeBot:** Sin límite oficial

## 🚀 INSTRUCCIONES PASO A PASO

### Para UltraMsg:
1. Ve a https://ultramsg.com/
2. Registrarse → Connect WhatsApp → Escanear QR
3. Copiar Instance ID y Token
4. Pegar en archivo `.env`
5. Reiniciar bot

### Para CallMeBot:
1. Enviar "I allow callmebot to send me messages" a +34 644 26 61 85
2. Esperar respuesta con API Key
3. Pegar API Key en `.env`  
4. Reiniciar bot

**¡Una vez configurado recibirás notificaciones instantáneas de cada lead!** 🎯