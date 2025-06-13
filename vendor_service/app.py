from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ariadne.asgi import GraphQL
from ariadne import load_schema_from_path, make_executable_schema
from resolvers import resolvers
from database import init_db
import uvicorn

type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(type_defs, resolvers)
graphql_app = GraphQL(schema, debug=True)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount GraphQL at root
app.mount("/", graphql_app)

@app.on_event("startup")
async def startup_event():
    await init_db()  # Tambahkan await di sini
    print("Vendor DB initialized")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8005, reload=True)