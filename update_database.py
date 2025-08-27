#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para actualizar la base de datos agregando campos de promoción
"""

import sqlite3
import logging

DATABASE = 'marketplace_bot.db'

def update_database():
    """Agregar campos de promoción a la tabla products"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Verificar si las columnas ya existen
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Agregar columnas de promoción si no existen
        new_columns = [
            ("discount_enabled", "BOOLEAN DEFAULT FALSE"),
            ("discount_name", "TEXT"),
            ("discount_min_quantity", "INTEGER DEFAULT 3"),
            ("discount_percentage", "REAL DEFAULT 10"),
            ("discount_description", "TEXT"),
            ("bulk_discounts", "TEXT")  # JSON con descuentos escalonados
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {column_name} {column_def}")
                print(f"+ Agregada columna: {column_name}")
            else:
                print(f"- Columna ya existe: {column_name}")
        
        # Insertar datos de ejemplo de promociones
        cursor.execute('''
            UPDATE products 
            SET discount_enabled = TRUE,
                discount_name = "Compra más, ahorra más",
                discount_min_quantity = 3,
                discount_percentage = 10,
                discount_description = "Descuentos especiales por cantidad",
                bulk_discounts = '{"3": 10, "4": 12, "5": 15, "6": 18}'
            WHERE key_name = 'tappers'
        ''')
        
        cursor.execute('''
            UPDATE products 
            SET discount_enabled = FALSE,
                discount_name = "",
                discount_min_quantity = 3,
                discount_percentage = 0,
                discount_description = "",
                bulk_discounts = '{}'
            WHERE key_name IN ('vasos', 'platos')
        ''')
        
        conn.commit()
        print("+ Base de datos actualizada correctamente")
        
        # Mostrar productos con promociones
        cursor.execute('''
            SELECT name, discount_enabled, discount_name, discount_percentage, bulk_discounts 
            FROM products
        ''')
        
        print("\n=== PRODUCTOS Y PROMOCIONES ===")
        for row in cursor.fetchall():
            status = "ACTIVA" if row[1] else "INACTIVA"
            print(f"{row[0]}: Promocion {status}")
            if row[1]:
                print(f"  - Nombre: {row[2]}")
                print(f"  - Descuento base: {row[3]}%")
                print(f"  - Descuentos escalonados: {row[4]}")
        
    except Exception as e:
        print(f"Error actualizando base de datos: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()