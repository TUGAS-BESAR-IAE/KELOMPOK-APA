import os
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dgpyzXndVtMpGAYlHuwBckOxnvwntmQy@postgres.railway.internal:5432/railway")

async def get_db_connection():
    database = Database(DATABASE_URL)
    await database.connect()
    return database

async def init_db():
    database = await get_db_connection()
    
    # Create vendors table first (uncomment ini)
    await database.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            contact_info TEXT
        )
    """)
    
    # Create vendor_transactions table (hapus comma trailing)
    await database.execute("""
        CREATE TABLE IF NOT EXISTS vendor_transactions (
            id SERIAL PRIMARY KEY,
            vendor_id INTEGER NOT NULL,
            livestock_type VARCHAR(50) CHECK(livestock_type IN ('sapi', 'ayam', 'kambing', 'domba')),
            total INTEGER NOT NULL,
            status VARCHAR(20) CHECK(status IN ('belum', 'sudah')) DEFAULT 'belum',
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    """)
    
    # Insert sample vendors if table is empty
    vendor_count = await database.fetch_val("SELECT COUNT(*) FROM vendors")
    if vendor_count == 0:
        await database.execute("""
            INSERT INTO vendors (name, contact_info) VALUES 
            ('PT Sapi Jaya', 'Jl. Raya No. 123, Telp: 081234567890'),
            ('CV Ternak Makmur', 'Jl. Merdeka No. 456, Telp: 081987654321'),
            ('UD Kambing Sejahtera', 'Jl. Pahlawan No. 789, Telp: 081122334455')
        """)
        print("Sample vendors berhasil ditambahkan.")
    
    print("Tabel 'vendors' dan 'vendor_transactions' berhasil dibuat.")
    await database.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
