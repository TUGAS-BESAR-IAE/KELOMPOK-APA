from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ariadne.asgi import GraphQL
from ariadne import load_schema_from_path, make_executable_schema
from database import init_db 
from resolvers import resolvers, sync_sapi_to_raw_material
import uvicorn

type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(type_defs, resolvers)

graphql_app = GraphQL(schema, debug=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/graphql", graphql_app)


@app.on_event("startup")
async def startup():
    init_db()
    print("Product DB initialized")
    sync_sapi_to_raw_material()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8003, reload=True)
