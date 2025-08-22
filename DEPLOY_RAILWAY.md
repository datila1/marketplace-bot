# 🚀 DEPLOY EN RAILWAY - GUÍA COMPLETA

## ¿Por qué Railway?
- ✅ $5 USD gratis mensual (suficiente para el bot)
- ✅ No se duerme (24/7 activo)
- ✅ Deploy automático desde GitHub
- ✅ Variables de entorno fáciles
- ✅ Base de datos PostgreSQL incluida

## 📋 PREPARAR EL PROYECTO

### 1. Crear archivos necesarios para Railway

#### `requirements.txt` (dependencias)
```
Flask==2.3.3
requests==2.31.0
python-dotenv==1.0.0
```

#### `Procfile` (comando de inicio)
```
web: python app.py
```

#### `runtime.txt` (versión de Python)
```
python-3.11.0
```

#### Modificar `app.py` para Railway
- Usar puerto dinámico: `port = int(os.environ.get('PORT', 5000))`
- Configurar para producción

## 🔧 PASOS PARA DEPLOY

### Paso 1: Crear cuenta en Railway
1. Ir a: https://railway.app/
2. Registrarse con GitHub
3. Conectar repositorio

### Paso 2: Subir código a GitHub
1. Crear repositorio en GitHub
2. Subir todos los archivos del bot
3. No subir `.env` (Railway maneja variables por separado)

### Paso 3: Deploy en Railway
1. "New Project" → "Deploy from GitHub repo"
2. Seleccionar tu repositorio
3. Railway detectará automáticamente que es Python/Flask
4. Deploy automático

### Paso 4: Configurar Variables de Entorno
En Railway dashboard → Variables:
```
PAGE_ACCESS_TOKEN=EAAJNMIKacyw...
FACEBOOK_APP_SECRET=b34b6e3f1e80...
VERIFY_TOKEN=mi_token_secreto_marketplace_2024
ULTRAMSG_TOKEN=c1r4yht635djnq7j
ULTRAMSG_INSTANCE=instance140130
OWNER_WHATSAPP=+59178056048
```

### Paso 5: Obtener URL de Railway
Railway te dará una URL como:
```
https://tu-bot-production.up.railway.app
```

### Paso 6: Configurar Webhook en Facebook
1. Facebook Developers → Tu app → Webhooks
2. URL: `https://tu-bot-production.up.railway.app/webhook`
3. Verify Token: `mi_token_secreto_marketplace_2024`

## 📊 VENTAJAS VS NGROK

| Característica | ngrok | Railway |
|----------------|--------|---------|
| Gratis | ✅ | ✅ |
| 24/7 activo | ❌ | ✅ |
| URL permanente | ❌ | ✅ |
| Auto-restart | ❌ | ✅ |
| Base de datos | ❌ | ✅ |
| SSL automático | ✅ | ✅ |

## 🔄 ALTERNATIVA: RENDER

Si prefieres Render:
1. https://render.com/
2. Mismo proceso, pero gratis con limitaciones
3. Se "duerme" después de 15 min sin uso
4. Se despierta automáticamente con el primer mensaje

## 💡 CONSEJOS

### Para Railway:
- Monitorea el uso en el dashboard
- $5/mes es suficiente para cientos de usuarios
- Si se agota, cuesta $5/mes extra

### Para Render (alternativa):
- Completamente gratis
- Perfecto si no tienes muchos usuarios
- Se despierta rápido (2-3 segundos)

## 🚀 ¿EMPEZAMOS CON RAILWAY?

Necesito que:
1. Crees cuenta en Railway.app
2. Crees repositorio en GitHub
3. Te ayudo a adaptar el código
4. Deploy automático