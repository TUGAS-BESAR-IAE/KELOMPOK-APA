from ariadne import QueryType, MutationType
from database import get_db_connection
import requests

ORDER_SERVICE_URL = "http://localhost:5001/graphql"  # Ganti dengan URL service order yang benar
USER_SERVICE_URL = "http://localhost:5000/graphql"  # Ganti dengan URL service user yang benar

query = QueryType()
mutation = MutationType()

def get_user_name(user_id):
    query = """
    query($id: ID!) {
        users {
            id
            name
        }
    }
    """
    # Ambil semua user, lalu cari yang id-nya cocok
    resp = requests.post(USER_SERVICE_URL, json={"query": query})
    users = resp.json().get("data", {}).get("users", [])
    for user in users:
        if str(user["id"]) == str(user_id):
            return user["name"]
    return "Unknown"

def get_user_id_from_order(order_id):
    query = """
    query($id: ID!) {
        orders {
            id
            user_id
        }
    }
    """
    resp = requests.post(ORDER_SERVICE_URL, json={"query": query})
    orders = resp.json().get("data", {}).get("orders", [])
    for order in orders:
        if str(order["id"]) == str(order_id):
            return order["user_id"]
    return None
@query.field("payments")
def resolve_payments(*_):
    conn = get_db_connection()
    payments = conn.execute("SELECT * FROM payments").fetchall()
    return [dict(row) for row in payments]

def generate_transaction_id(conn, status):
    count = conn.execute("SELECT COUNT(*) FROM payments WHERE payment_status = ?", (status,)).fetchone()[0] + 1
    prefix = {
        "pending": "PDG",
        "paid": "PAID",
        "failed": "FLD",
        "expired": "EXP"
    }.get(status, "UNK")
    return f"{prefix}{count:03d}"

@mutation.field("addPayment")
def resolve_add_payment(_, info, order_id, payment_method, amount, payment_status, transaction_id=None):
    print("== addPayment Called ==")
    print(f"Order ID: {order_id}, Method: {payment_method}, Amount: {amount}, Status: {payment_status}")

    conn = get_db_connection()
    transaction_id = generate_transaction_id(conn, payment_status)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO payments (order_id, payment_method, amount, payment_status, transaction_id) VALUES (?, ?, ?, ?, ?)",
        (order_id, payment_method, amount, payment_status, transaction_id)
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM payments WHERE id = ?", (new_id,)).fetchone()
    print("== insert success ==")
    return dict(row)

resolvers = [query, mutation]
