from ariadne import QueryType, MutationType
from database import get_db_connection
import requests
import asyncio

query = QueryType()
mutation = MutationType()

@query.field("ping")
def resolve_ping(_, info):
    return "pong"

@query.field("vendors")
async def resolve_vendors(_, info):
    database = await get_db_connection()
    
    try:
        rows = await database.fetch_all("SELECT id, name, contact_info FROM vendors")
        vendors = []
        for row in rows:
            vendors.append({
                "id": row["id"],
                "name": row["name"],
                "contact_info": row["contact_info"]
            })
        return vendors
    except Exception as e:
        print(f"Error fetching vendors: {e}")
        return []
    finally:
        await database.disconnect()

@query.field("vendorTransactions")
async def resolve_vendor_transactions(_, info, vendor_id):
    database = await get_db_connection()
    
    try:
        rows = await database.fetch_all("""
            SELECT vt.id, vt.vendor_id, vt.livestock_type, vt.total, vt.status, vt.transaction_date, 
                   COALESCE(v.name, 'Unknown Vendor') as name
            FROM vendor_transactions vt
            LEFT JOIN vendors v ON vt.vendor_id = v.id
            WHERE vt.vendor_id = :vendor_id
        """, {"vendor_id": vendor_id})
        
        transactions = []
        for row in rows:
            transactions.append({
                "id": row["id"],
                "vendor_id": row["vendor_id"],
                "livestock_type": row["livestock_type"],
                "total": row["total"],
                "status": row["status"],
                "transaction_date": row["transaction_date"],
                "vendor_name": row["name"]
            })
        return transactions
    except Exception as e:
        print(f"Error fetching vendor transactions: {e}")
        return []
    finally:
        await database.disconnect()

@query.field("vendorTransactionsAll")
async def resolve_vendor_transactions_all(_, info):
    database = await get_db_connection()
    
    try:
        rows = await database.fetch_all("""
            SELECT vt.*, COALESCE(v.name, 'Unknown Vendor') as vendor_name
            FROM vendor_transactions vt
            LEFT JOIN vendors v ON vt.vendor_id = v.id
            ORDER BY vt.transaction_date DESC
        """)
        
        return [
            {
                "id": row["id"],
                "vendor_id": row["vendor_id"],
                "vendor_name": row["vendor_name"],
                "livestock_type": row["livestock_type"],
                "total": row["total"],
                "status": row["status"],
                "transaction_date": row["transaction_date"]
            }
            for row in rows
        ]
    except Exception as e:
        print(f"Error fetching all vendor transactions: {e}")
        return []
    finally:
        await database.disconnect()

@mutation.field("addVendorTransaction")
async def resolve_add_vendor_transaction(_, info, vendor_id, livestock_type, total):
    database = await get_db_connection()
    
    # Insert new transaction
    transaction = await database.fetch_one("""
        INSERT INTO vendor_transactions (vendor_id, livestock_type, total)
        VALUES (:vendor_id, :livestock_type, :total)
        RETURNING id, vendor_id, livestock_type, total, status, transaction_date
    """, {"vendor_id": vendor_id, "livestock_type": livestock_type, "total": total})

    # Get vendor name
    vendor = await database.fetch_one(
        "SELECT name FROM vendors WHERE id = :vendor_id", 
        {"vendor_id": vendor_id}
    )
    vendor_name = vendor["name"] if vendor else None

    await database.disconnect()

    return {
        "id": transaction["id"],
        "vendor_id": transaction["vendor_id"],
        "livestock_type": transaction["livestock_type"],
        "total": transaction["total"],
        "status": transaction["status"],
        "transaction_date": transaction["transaction_date"],
        "vendor_name": vendor_name
    }

@mutation.field("updateTransactionStatus")
async def resolve_update_transaction_status(_, info, transaction_id, status):
    database = await get_db_connection()

    # Check if transaction exists
    transaction = await database.fetch_one(
        "SELECT * FROM vendor_transactions WHERE id = :transaction_id", 
        {"transaction_id": transaction_id}
    )

    if not transaction:
        await database.disconnect()
        return None

    # Update transaction status
    updated = await database.fetch_one("""
        UPDATE vendor_transactions SET status = :status
        WHERE id = :transaction_id
        RETURNING *
    """, {"status": status, "transaction_id": transaction_id})

    # Debug log
    print(">> Status akan diupdate ke:", status)
    print(">> Data transaksi:", dict(updated))

    # If status is "sudah", sync with product service
    if status.lower() == "sudah":
        mutation_query = """
        mutation($vendor_transaction_id: Int, $livestock_type: String!, $quantity: Int!) {
            addRawMaterial(vendor_transaction_id: $vendor_transaction_id, livestock_type: $livestock_type, quantity: $quantity) {
                id
            }
        }
        """
        variables = {
            "vendor_transaction_id": updated["id"],
            "livestock_type": updated["livestock_type"].lower(),
            "quantity": updated["total"]
        }

        try:
            print(">> Mengirim request ke product_service...")
            response = requests.post(
                "http://product_service:8003/graphql",
                json={"query": mutation_query, "variables": variables},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print(">> Response product_service:", response.text)
        except Exception as e:
            print("[ERROR]: Gagal sinkron ke product_service:", e)

    # Get vendor name
    vendor = await database.fetch_one(
        "SELECT name FROM vendors WHERE id = :vendor_id", 
        {"vendor_id": updated["vendor_id"]}
    )
    vendor_name = vendor["name"] if vendor else None

    await database.disconnect()

    return {
        "id": updated["id"],
        "vendor_id": updated["vendor_id"],
        "livestock_type": updated["livestock_type"],
        "total": updated["total"],
        "status": updated["status"],
        "transaction_date": updated["transaction_date"],
        "vendor_name": vendor_name
    }

resolvers = [query, mutation]
