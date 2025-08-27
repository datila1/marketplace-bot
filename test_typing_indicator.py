#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test del indicador de escritura realista
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import calculate_realistic_typing_time

def test_typing_times():
    """Probar tiempos de escritura realistas"""
    
    print("=== TEST INDICADOR DE ESCRITURA ===\n")
    
    # Mensajes de prueba de diferentes longitudes
    test_messages = [
        "Hola",
        "Sí, tenemos a 35bs",
        "Ok, 3 vasos en 32bs con descuento de 4bs",
        "Nada menos estimado, pero si lleva 3 le hago 10% descuento = 95bs con envío gratis hasta el cuarto anillo",
        "Perfecto! Para coordinar entrega, escribeme por WhatsApp: wa.me/59178056048. Tenemos horarios flexibles y entrega el mismo día en Santa Cruz."
    ]
    
    print("Tiempos de escritura calculados:")
    print("-" * 60)
    
    for i, message in enumerate(test_messages, 1):
        typing_time = calculate_realistic_typing_time(message)
        char_count = len(message)
        
        print(f"{i}. Mensaje: '{message[:50]}{'...' if len(message) > 50 else ''}'")
        print(f"   Caracteres: {char_count}")
        print(f"   Tiempo de escritura: {typing_time} segundos")
        print()
    
    print("=== COMO FUNCIONARÁ ===")
    print("1. Usuario envía: 'quiero vasos'")
    print("2. Bot muestra: 'escribiendo...' por ~2 segundos")
    print("3. Bot responde: 'Sí, tenemos a 12bs'")
    print()
    print("4. Usuario envía: 'ok, dame 3'")
    print("5. Bot muestra: 'escribiendo...' por ~4 segundos")
    print("6. Bot responde: 'Ok, 3 vasos en 32bs con descuento...'")
    print()
    print("¡El bot ahora se siente mucho más humano y natural!")

if __name__ == "__main__":
    test_typing_times()