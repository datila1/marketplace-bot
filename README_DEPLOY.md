# 🤖 Marketplace Bot - Facebook Messenger

Bot inteligente para Facebook Messenger con sistema de descuentos, detección de género y notificaciones WhatsApp.

## 🚀 DEPLOY EN RAILWAY (RECOMENDADO)

### ✅ Pre-requisitos
- Cuenta en Railway.app
- Cuenta en GitHub
- Tokens de Facebook configurados

### 📋 Pasos de Deploy

#### 1. Preparar Repositorio
```bash
git init
git add .
git commit -m "Initial commit - Marketplace Bot"
git remote add origin https://github.com/TU_USUARIO/marketplace-bot.git
git push -u origin main
```

#### 2. Deploy en Railway
1. Ir a: https://railway.app/
2. "New Project" → "Deploy from GitHub repo"
3. Seleccionar repositorio
4. Deploy automático

#### 3. Configurar Variables de Entorno
En Railway Dashboard → Variables:
```
PAGE_ACCESS_TOKEN=TU_TOKEN_AQUI
FACEBOOK_APP_SECRET=TU_APP_SECRET
VERIFY_TOKEN=mi_token_secreto_marketplace_2024
ULTRAMSG_TOKEN=c1r4yht635djnq7j
ULTRAMSG_INSTANCE=instance140130
OWNER_WHATSAPP=+59178056048
PORT=5000
DEBUG=False
```

#### 4. Configurar Webhook Facebook
URL: `https://TU-APP.up.railway.app/webhook`

## 🔄 ALTERNATIVA: RENDER

### Deploy en Render (Gratis con limitaciones)
1. https://render.com/
2. Conectar GitHub
3. Configurar como "Web Service"
4. Variables de entorno iguales

## 📊 Características

- ✅ Conversación natural en español
- ✅ Sistema de descuentos tirado (3 = 95bs)
- ✅ Detección de género (estimado/estimada)
- ✅ Gestión delivery/recojo
- ✅ Notificaciones WhatsApp automáticas
- ✅ Panel de administración
- ✅ Base de datos PostgreSQL/SQLite
- ✅ Retraso de 4 segundos (mensaje 3+)

## 🏗️ Arquitectura

```
Usuario Facebook → Webhook → Bot Logic → WhatsApp + DB
```

## 📱 Flujo Conversacional

### Caso 1: Compra Directa
```
👤 "quiero tappers"
🤖 "Sí, tenemos a 35bs"
👤 "quiero 3"
🤖 "ok si quiere 3 te hago un descuento de 10bs, 3 tapper en 95bs"
👤 "si me parece bien, hacen entrega a domicilio?"
🤖 "si, pero la entrega no incluye el precio, usted tendria que pagar por el delivery, o caso contrario podria recogerlo del almacen"
```

## 🔧 Desarrollo Local

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python app.py
```

## 🚀 Beneficios del Deploy

| Aspecto | Local + ngrok | Railway |
|---------|---------------|---------|
| Disponibilidad | Solo cuando PC esté encendida | 24/7 |
| URL | Cambia cada restart | Permanente |
| SSL | Automático | Automático |
| Base de datos | SQLite local | PostgreSQL |
| Backups | Manual | Automático |
| Escalabilidad | Limitada | Alta |

## 📈 Monitoreo

- **Logs**: Railway Dashboard → Logs
- **Métricas**: Panel admin en `/admin`
- **Base de datos**: Railway Dashboard → Data

## 💰 Costos

- **Railway**: $5 USD/mes de crédito gratis
- **Render**: Completamente gratis (con "sleep")
- **Tu bot actual**: ~$0.50/mes de uso estimado