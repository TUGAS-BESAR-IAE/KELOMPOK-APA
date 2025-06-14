from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
# import requests
# from fastapi import APIRouter

app = FastAPI()

# Static and template
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/login.html")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/do_login")
async def do_login():
    response = RedirectResponse(url="/users")
    response.set_cookie("is_logged_in", "true")
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login.html")
    response.delete_cookie("is_logged_in")  # penting: hapus cookie login
    return response

@app.get("/users")
@app.get("/users.html")
async def users_page(request: Request):
    if request.cookies.get("is_logged_in") != "true":
        return RedirectResponse(url="/login.html")
    return templates.TemplateResponse("users.html", {"request": request})

@app.get("/payment")
async def payment_page(request: Request):
    if request.cookies.get("is_logged_in") != "true":
        return RedirectResponse(url="/login.html")
    return templates.TemplateResponse("payment.html", {"request": request})

@app.get("/vendor")
@app.get("/vendors")
@app.get("/vendors.html")
async def vendors_page(request: Request):
    if request.cookies.get("is_logged_in") != "true":
        return RedirectResponse(url="/login.html")
    return templates.TemplateResponse("vendors.html", {"request": request})

@app.get("/products")
@app.get("/products.html")
async def products_page(request: Request):
    if request.cookies.get("is_logged_in") != "true":
        return RedirectResponse(url="/login.html")
    return templates.TemplateResponse("products.html", {"request": request})

@app.get("/orders")
@app.get("/orders.html")
async def orders_page(request: Request):
    if request.cookies.get("is_logged_in") != "true":
        return RedirectResponse(url="/login.html")
    return templates.TemplateResponse("orders.html", {"request": request})

# @app.get("/api/users")
# async def get_users():
#     query = {
#         "query": """
#             query {
#                 users {
#                     id
#                     name
#                 }
#             }
#         """
#     }
#     try:
#         res = requests.post("http://user_service:8001/graphql", json=query)
#         return res.json()["data"]["users"]
#     except Exception as e:
#         print("❌ Gagal fetch users:", e)
#         return []

# @app.get("/api/products")
# async def get_products():
#     query = {
#         "query": """
#             query {
#                 products {
#                     id
#                     name
#                     quantity
#                 }
#             }
#         """
#     }
#     try:
#         res = requests.post("http://product_service:8003/graphql", json=query)
#         return res.json()["data"]["products"]
#     except Exception as e:
#         print("❌ Gagal fetch products:", e)
#         return []



# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)