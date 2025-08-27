#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para configurar promociones atractivas en los productos
"""

import sqlite3
import json

DATABASE = 'marketplace_bot.db'

def setup_attractive_promotions():
    """Configurar promociones atractivas para productos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Promociones diseñadas para maximizar ventas
    promotions = {
        'tappers': {
            'enabled': True,
            'name': '¡MEGA AHORRO! Compra más, paga menos',
            'min_quantity': 3,
            'base_percentage': 12,
            'description': 'Promoción especial de tappers. ¡Ideal para toda la familia!',
            'bulk_discounts': {
                '3': 12,    # 3 tappers: 12% descuento (93bs en lugar de 105bs)
                '5': 18,    # 5 tappers: 18% descuento (143bs en lugar de 175bs)
                '10': 25,   # 10 tappers: 25% descuento (263bs en lugar de 350bs)
                '20': 30    # 20+ tappers: 30% descuento (490bs en lugar de 700bs)
            }
        },
        'vasos': {
            'enabled': True,
            'name': 'OFERTA ESPECIAL - Vasos de Calidad',
            'min_quantity': 4,
            'base_percentage': 15,
            'description': 'Perfectos para el hogar. Resistentes y duraderos.',
            'bulk_discounts': {
                '4': 15,    # 4 vasos: 15% descuento (41bs en lugar de 48bs)
                '6': 20,    # 6 vasos: 20% descuento (58bs en lugar de 72bs)
                '12': 25    # 12+ vasos: 25% descuento (108bs en lugar de 144bs)
            }
        },
        'platos': {
            'enabled': True,
            'name': 'LIQUIDACIÓN - Platos Premium',
            'min_quantity': 2,
            'base_percentage': 20,
            'description': 'Últimas unidades a precio especial. ¡No te pierdas esta oportunidad!',
            'bulk_discounts': {
                '2': 20,    # 2 platos: 20% descuento (32bs en lugar de 40bs)
                '4': 25,    # 4 platos: 25% descuento (60bs en lugar de 80bs)
                '6': 30     # 6+ platos: 30% descuento (84bs en lugar de 120bs)
            }
        }
    }
    
    print("=== CONFIGURANDO PROMOCIONES ATRACTIVAS ===\n")
    
    for product_key, promo in promotions.items():
        cursor.execute('''
            UPDATE products 
            SET discount_enabled = ?,
                discount_name = ?,
                discount_min_quantity = ?,
                discount_percentage = ?,
                discount_description = ?,
                bulk_discounts = ?
            WHERE key_name = ?
        ''', (
            promo['enabled'],
            promo['name'],
            promo['min_quantity'],
            promo['base_percentage'],
            promo['description'],
            json.dumps(promo['bulk_discounts']),
            product_key
        ))
        
        # Mostrar información de la promoción configurada
        cursor.execute('SELECT name, price FROM products WHERE key_name = ?', (product_key,))
        result = cursor.fetchone()
        if result:
            product_name, price = result
            print(f"+ {product_name.upper()}:")
            print(f"  Promocion: {promo['name']}")
            print(f"  Precio unitario: {price}bs")
            print(f"  Minimo para descuento: {promo['min_quantity']} unidades")
            print(f"  Descuentos disponibles:")
            
            for qty, discount in promo['bulk_discounts'].items():
                qty_num = int(qty)
                total_normal = qty_num * price
                discount_amount = (total_normal * discount) / 100
                total_with_discount = total_normal - discount_amount
                savings = discount_amount
                
                print(f"    - {qty} unidades: {discount}% OFF = {total_with_discount:.0f}bs (ahorras {savings:.0f}bs)")
            print()
    
    conn.commit()
    
    # Mostrar resumen de todas las promociones activas
    cursor.execute('''
        SELECT name, discount_name, discount_min_quantity, bulk_discounts, price
        FROM products 
        WHERE discount_enabled = TRUE
        ORDER BY name
    ''')
    
    active_promos = cursor.fetchall()
    print("=== RESUMEN DE PROMOCIONES ACTIVAS ===")
    for name, promo_name, min_qty, bulk_json, price in active_promos:
        discounts = json.loads(bulk_json)
        best_discount = max(discounts.values()) if discounts else 0
        print(f"- {name}: Hasta {best_discount}% de descuento desde {min_qty} unidades")
    
    conn.close()
    print(f"\nPromociones configuradas exitosamente!")
    print("Ahora el chatbot solo aplicara descuentos si las promociones estan HABILITADAS.")

if __name__ == "__main__":
    setup_attractive_promotions()