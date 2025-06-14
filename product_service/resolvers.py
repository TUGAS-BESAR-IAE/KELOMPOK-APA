from ariadne import QueryType, MutationType
from database import get_db_connection
import requests

query = QueryType()
mutation = MutationType()


def update_sapi_stok(sapi_id, stok_baru):
    mutation = """
    mutation($id: Int!, $stok: Int!) {
        updateSapi(id: $id, stok: $stok) {
            id
        }
    }
    """
    try:
        res = requests.post(
            "https://sapiservice-production.up.railway.app/",
            json={"query": mutation, "variables": {"id": sapi_id, "stok": stok_baru}},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return res.json()
    except Exception as e:
        print("❌ Gagal update sapi:", e)
        return None

def delete_sapi(id):
    mutation = """
    mutation($id: Int!) {
        deleteSapi(id: $id)
    }
    """
    try:
        res = requests.post(
            "https://sapiservice-production.up.railway.app/",
            json={"query": mutation, "variables": {"id": id}},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return res.json()
    except Exception as e:
        print("❌ Gagal delete sapi:", e)
        return None
    
def sync_sapi_to_raw_material():
    print("🚀 Mulai sync dari kelompok lain...")
    query = """
    query {
        sapis {
            id
            berat
            harga
            stok
            umur
        }
    }
    """
    try:
        response = requests.post(
            "https://sapiservice-production.up.railway.app/",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        data = response.json()
        print("📦 Data dari kelompok lain:", data)

        sapi_list = data.get("data", {}).get("sapis", [])
        if not sapi_list:
            print("⚠️ Tidak ada data sapi ditemukan.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM raw_materials")  # bersihkan dulu biar nggak dobel

        for sapi in sapi_list:
            cursor.execute(
                "INSERT INTO raw_materials (id, livestock_type, quantity) VALUES (?, ?, ?)",
                (sapi["id"], "sapi", sapi["stok"])
            )

        conn.commit()
        conn.close()
        print(f"✅ Sinkronisasi berhasil, {len(sapi_list)} sapi ditambahkan.")

    except Exception as e:
        print("❌ Gagal sync dari service sapi:", e)

    
@query.field("rawMaterials")
def resolve_raw_materials(_, info):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM raw_materials")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@query.field("products")
def resolve_products(_, info):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@mutation.field("addRawMaterial")
def resolve_add_raw_material(_, info, vendor_transaction_id=None, livestock_type="", quantity=0):
    # Validate livestock_type
    if livestock_type not in ['sapi', 'ayam', 'kambing', 'domba']:
        raise ValueError("Invalid livestock_type. Must be one of: sapi, ayam, kambing, domba")

    # Validate quantity
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    conn = get_db_connection()
    c = conn.cursor()

    # Check if vendor_transaction_id already exists
    if vendor_transaction_id:
        c.execute("SELECT id FROM raw_materials WHERE vendor_transaction_id = ?", (vendor_transaction_id,))
        if c.fetchone():
            conn.close()
            raise ValueError("Raw material for this vendor transaction already exists")

    # Tambahkan raw material
    c.execute('''
        INSERT INTO raw_materials (vendor_transaction_id, livestock_type, quantity)
        VALUES (?, ?, ?)
        RETURNING *
    ''', (vendor_transaction_id, livestock_type, quantity))
    row = c.fetchone()

    conn.commit()
    conn.close()
    return dict(row)

@mutation.field("decreaseRawMaterial")
def resolve_decrease_raw_material(_, info, id, amount):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT quantity FROM raw_materials WHERE id = ?", (id,))
    row = c.fetchone()
    if not row:
        raise ValueError("Raw material not found")

    new_qty = max(0, row["quantity"] - amount)
    c.execute("UPDATE raw_materials SET quantity = ? WHERE id = ?", (new_qty, id))

    # Sync ke service sapi
    update_sapi_stok(id, new_qty)

    conn.commit()
    c.execute("SELECT * FROM raw_materials WHERE id = ?", (id,))
    updated = c.fetchone()
    conn.close()
    return dict(updated)

@mutation.field("deleteRawMaterial")
def resolve_delete_raw_material(_, info, id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM raw_materials WHERE id = ?", (id,))

    # Hapus juga dari service sapi
    delete_sapi(id)

    conn.commit()
    conn.close()
    return True


@mutation.field("addProduct")
def resolve_add_product(_, info, raw_material_id, name, unit, quantity):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO products (raw_material_id, name, unit, quantity)
        VALUES (?, ?, ?, ?)
        RETURNING *
    ''', (raw_material_id, name, unit, quantity))
    row = c.fetchone()
    conn.commit()
    conn.close()
    return dict(row)

resolvers = [query, mutation]
