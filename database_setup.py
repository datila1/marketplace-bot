#!/usr/bin/env python3
"""
Configuración de base de datos para Railway
Maneja tanto SQLite (desarrollo) como PostgreSQL (producción)
"""

import os
import sqlite3

def setup_database():
    """Configurar base de datos según el entorno"""
    
    # En Railway, usar PostgreSQL si está disponible
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql://'):
        print("🐘 Configurando PostgreSQL para producción...")
        return setup_postgresql(database_url)
    else:
        print("🗄️ Usando SQLite para desarrollo...")
        return setup_sqlite()

def setup_postgresql(database_url):
    """Configurar PostgreSQL para producción"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parsear URL de conexión
        result = urlparse(database_url)
        
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        
        cursor = conn.cursor()
        
        # Crear tablas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                lead_captured BOOLEAN DEFAULT FALSE,
                phone_number TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                products_mentioned TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                key_name TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock INTEGER DEFAULT 0,
                keywords TEXT NOT NULL,
                description TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ PostgreSQL configurado correctamente")
        return conn, 'postgresql'
        
    except ImportError:
        print("❌ psycopg2 no instalado. Agregando a requirements...")
        # Fallback a SQLite si no hay psycopg2
        return setup_sqlite()
    except Exception as e:
        print(f"❌ Error configurando PostgreSQL: {e}")
        return setup_sqlite()

def setup_sqlite():
    """Configurar SQLite para desarrollo"""
    database_name = os.getenv('DATABASE_NAME', 'marketplace_bot.db')
    
    conn = sqlite3.connect(database_name, check_same_thread=False)
    cursor = conn.cursor()
    
    # Crear tablas SQLite (como ya tienes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            lead_captured BOOLEAN DEFAULT 0,
            phone_number TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            products_mentioned TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            keywords TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    print("✅ SQLite configurado correctamente")
    return conn, 'sqlite'

if __name__ == "__main__":
    conn, db_type = setup_database()
    print(f"Base de datos lista: {db_type}")
    conn.close()