# 🔄 Diagrama de Flujo Conversacional - Marketplace Bot

## Diagrama Principal (Mermaid)

```mermaid
flowchart TD
    A[👤 USUARIO ENVÍA MENSAJE] --> B{🔍 Analizar Mensaje}
    
    B --> C{¿Contiene nombre?}
    C -->|Sí| C1[💾 Detectar género<br/>María→estimada<br/>Carlos→estimado]
    C -->|No| D
    C1 --> D
    
    D{¿Es saludo?} -->|Sí| D1[👋 "Hola, ¿en qué te puedo ayudar?"]
    D -->|No| E
    
    E{¿Menciona producto?} -->|Sí| E1[💰 "Sí, tenemos a 35bs"]
    E -->|No| F
    
    F{¿Pregunta precio?} -->|Sí| F1{¿Producto específico?}
    F1 -->|Sí| F2[💵 "35 bs"]
    F1 -->|No| F3[📋 Lista todos los precios]
    F -->|No| G
    
    G{¿Menciona cantidad?} -->|Sí| G1{¿Es consulta o compra?}
    G1 -->|Consulta| G2[ℹ️ Precio + descuento<br/>SIN pedir teléfono]
    G1 -->|Compra| G3[💳 Precio + descuento<br/>+ "Deme su teléfono"]
    G -->|No| H
    
    H{¿Es negociación?} -->|Sí| H1{¿Menciona cantidad?}
    H1 -->|Sí| H2[🤝 Calcular descuento<br/>con género correcto]
    H1 -->|No| H3[💡 "Nada menos estimado/a,<br/>pero 3 unidades = 5% desc"]
    H -->|No| I
    
    I{¿Es confirmación?} -->|Sí| I1{¿Ya tiene cantidad?}
    I1 -->|Sí| I2[✅ Procesar cantidad]
    I1 -->|No| I3[❓ "¿Cuántos quiere?"]
    I -->|No| J
    
    J{¿Es número teléfono?} -->|Sí| K[📱 CAPTURAR LEAD]
    J -->|No| L[🤖 Respuesta por defecto]
    
    K --> K1[💾 Guardar en BD]
    K1 --> K2[📲 Enviar WhatsApp]
    K2 --> K3[✅ "Ok, ya te escribo al WhatsApp"]
    
    G2 --> M[🔄 Continuar conversación]
    G3 --> N[⏳ Esperar teléfono]
    F2 --> M
    F3 --> M
    E1 --> M
    D1 --> M
    H2 --> M
    H3 --> M
    I2 --> N
    I3 --> M
    L --> M
    K3 --> O[🏁 FIN]
    
    style A fill:#e1f5fe
    style K fill:#c8e6c9
    style O fill:#ffcdd2
```

## Flujo Detallado por Casos

### 📱 **CASO 1: Consulta Simple**
```
Usuario: "tappers"
Bot: "Sí, tenemos a 35bs"
Usuario: "precio?"  
Bot: "35 bs"
```

### 🛒 **CASO 2: Compra Directa**
```
Usuario: "quiero tappers"
Bot: "Sí, tenemos a 35bs"
Usuario: "quiero 3"
Bot: "Excelente! 3 tapper en 100bs (5% descuento) se aplica mayor descuento apartir de 5 unidades. Deme su teléfono"
Usuario: "78123456"
Bot: "Ok, ya te escribo al WhatsApp"
```

### 🤝 **CASO 3: Negociación**
```
Usuario: "tappers"
Bot: "Sí, tenemos a 35bs"
Usuario: "nada menos?"
Bot: "Nada menos estimado/a, pero si lleva 3 le hago 5% descuento = 100bs con envío gratis"
Usuario: "y 5?"
Bot: "5 tapper en 161bs (8% descuento) se aplica mayor descuento apartir de 7 unidades"
```

### 👥 **CASO 4: Con Detección de Género**
```
Usuario: "Hola, mi nombre es María"
Bot: "Hola, ¿en qué te puedo ayudar?"
Usuario: "tappers"
Bot: "Sí, tenemos a 35bs"
Usuario: "nada menos?"
Bot: "Nada menos estimada, pero si lleva 3 le hago 5% descuento = 100bs"
```

## ⚙️ Lógica de Decisiones

### 🔍 **Detección de Consulta vs Compra**
- **Consulta**: "y 3 no me hace precio?", "y 5 tapper?", "en cuanto?"
- **Compra**: "quiero 3", "llevo 5", "dame 4"

### 💰 **Sistema de Descuentos**
```
1 unidad  = 35bs (0%)
2 unidades = 70bs (0%) 
3 unidades = 100bs (5% desc)
4 unidades = 133bs (5% desc) → "se aplica mayor descuento apartir de 5"
5 unidades = 161bs (8% desc) → "se aplica mayor descuento apartir de 7"  
6 unidades = 193bs (8% desc) → "se aplica mayor descuento apartir de 7"
7+ unidades = 10% desc → sin mensaje adicional
```

### 👤 **Detección de Género**
- **Nombres femeninos**: María, Ana, Carmen → "estimada"
- **Nombres masculinos**: Carlos, Juan, Pedro → "estimado"
- **Sin nombre**: "estimado(a)"

## 🚨 Casos Especiales

### ❌ **Errores Comunes Corregidos**
1. **"ok quiero 1"** → Ahora procesa directamente (antes preguntaba "¿Cuántos quiere?")
2. **Consultas de precio** → No piden teléfono inmediatamente  
3. **Negociación sin cantidad** → Ofrece 3 unidades (no 2)
4. **Formato singular** → "4 tapper" (no "4 Tappers")

### 🔄 **Prioridad de Detección**
1. Teléfono (más alta prioridad)
2. Negociación con cantidad específica
3. Cantidad (antes que precio)
4. Pregunta de precio
5. Producto
6. Confirmación
7. Saludos/despedidas

---

## 📊 Métricas de Conversión

- **Leads capturados**: Conversaciones que llegan al teléfono
- **Tasa de descuento**: % mensajes con descuentos aplicados  
- **Abandono**: Conversaciones sin completar
- **Productos más consultados**: Tappers, vasos, platos