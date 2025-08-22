# Bot de Facebook Marketplace

Bot automatizado para ventas en Facebook Marketplace con respuestas directas y captura de leads.

## 🚀 Características

- **Respuestas súper directas** para maximizar conversiones
- **Base de datos SQLite** para almacenar conversaciones y leads
- **Detección automática de productos**: tappers (35bs), vasos (12bs), platos (20bs)
- **Captura automática de teléfonos** como leads de ventas
- **Panel de administración web** en `/admin`
- **API endpoints** para testing y analytics
- **Logging detallado** para monitoreo

## 📋 Productos Disponibles

| Producto | Precio | Keywords |
|----------|--------|----------|
| Tappers | 35 bs | tapper, tappers, recipiente, contenedor |
| Vasos | 12 bs | vaso, vasos, copa, copas |
| Platos | 20 bs | plato, platos, plato hondo, plato llano |

## 💬 Flujo de Conversación Objetivo

```
Cliente: "Tappers"
Bot: "Sí"

Cliente: "Precio?"
Bot: "35 bs"

Cliente: "Dos"
Bot: "Ok. Deme su teléfono"

Cliente: "78056048"
Bot: "Ok, ya te escribo al WhatsApp"
```

## 🛠️ Instalación

### Requisitos Previos
- Python 3.8 or superior
- pip (administrador de paquetes de Python)

### Pasos de Instalación

1. **Clonar/Descargar el proyecto**
```bash
cd ~/Desktop
cd marketplace-bot-local
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
   - Editar el archivo `.env` con tus tokens de Facebook
   - Configurar el `VERIFY_TOKEN` y `PAGE_ACCESS_TOKEN`

4. **Ejecutar el bot**
```bash
python app.py
```

## 🔧 Configuración

### Variables de Entorno (.env)

- `VERIFY_TOKEN`: Token de verificación para Facebook webhook
- `PAGE_ACCESS_TOKEN`: Token de acceso de tu página de Facebook
- `PORT`: Puerto del servidor (default: 5000)
- `DEBUG`: Modo debug (True/False)

### Facebook Messenger Setup

1. Crear una app en Facebook Developers
2. Configurar Messenger Platform
3. Generar Page Access Token
4. Configurar webhook URL: `https://tu-dominio.com/webhook`
5. Suscribirse a eventos de mensajes

## 🌐 Endpoints API

### `/webhook` (GET/POST)
- **GET**: Verificación del webhook de Facebook
- **POST**: Recibe mensajes de Facebook Messenger

### `/test` (GET/POST)
- **GET**: Interfaz web para probar el bot localmente
- **POST**: Envía mensajes de prueba al bot

### `/admin` (GET)
Panel de administración con:
- Estadísticas de conversaciones
- Lista de leads capturados
- Historial de conversaciones
- Métricas de usuarios únicos

### `/analytics` (GET)
API de analytics con:
- Productos más consultados
- Conversaciones por día
- Estadísticas en formato JSON

## 🗃️ Base de Datos

### Tabla: conversations
```sql
- id: INTEGER PRIMARY KEY
- user_id: TEXT (ID del usuario de Facebook)
- message: TEXT (mensaje del usuario)
- bot_response: TEXT (respuesta del bot)
- timestamp: DATETIME
- lead_captured: BOOLEAN
- phone_number: TEXT
```

### Tabla: leads
```sql
- id: INTEGER PRIMARY KEY  
- user_id: TEXT UNIQUE (ID del usuario de Facebook)
- phone_number: TEXT (teléfono capturado)
- products_interested: TEXT (productos de interés en JSON)
- timestamp: DATETIME
- status: TEXT (estado del lead: new, contacted, converted)
```

## 🧪 Testing Local

1. **Ejecutar el servidor**
```bash
python app.py
```

2. **Abrir en navegador**
```
http://localhost:5000/test
```

3. **Probar conversaciones**
   - Escribir mensajes como "tappers", "precio", "dos", "78056048"
   - Verificar respuestas automáticas del bot

## 📊 Panel de Administración

Acceder a `http://localhost:5000/admin` para ver:

- **Estadísticas generales**
  - Total de conversaciones
  - Leads capturados
  - Usuarios únicos

- **Leads capturados**
  - Lista completa de teléfonos
  - Productos de interés
  - Fechas de captura

- **Últimas conversaciones**
  - Historial reciente
  - Respuestas del bot
  - Timestamps

## 🔍 Logging

El bot genera logs detallados en:
- **Consola**: Logs en tiempo real
- **Archivo**: `bot.log` (configurable en .env)

Niveles de log:
- `INFO`: Conversaciones guardadas, leads capturados
- `DEBUG`: Detalles de procesamiento de mensajes
- `ERROR`: Errores de base de datos o API

## 🚀 Deployment

### Desarrollo Local con ngrok
```bash
# Instalar ngrok
ngrok http 5000

# Usar la URL https de ngrok como webhook en Facebook
```

### Producción
- Subir a un servidor con HTTPS
- Configurar variables de entorno de producción
- Usar una base de datos más robusta (PostgreSQL)
- Implementar autenticación en endpoints administrativos

## 📁 Estructura del Proyecto

```
marketplace-bot-local/
├── app.py                 # Aplicación principal del bot
├── requirements.txt       # Dependencias de Python
├── .env                  # Variables de entorno
├── README.md             # Documentación
├── marketplace_bot.db    # Base de datos SQLite (se crea automáticamente)
└── bot.log              # Archivo de logs (se crea automáticamente)
```

## 🛡️ Seguridad

- **No commitear** el archivo `.env` con tokens reales
- **Usar HTTPS** en producción para webhooks
- **Validar tokens** en todas las peticiones de Facebook
- **Sanitizar inputs** de usuarios antes de guardar en BD

## 🤝 Contribuir

1. Fork del proyecto
2. Crear branch para nueva feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Revisar los logs en `bot.log`
- Verificar configuración en `.env`

---

**Desarrollado para automatizar ventas en Facebook Marketplace con respuestas directas y efectivas** 🤖💼
