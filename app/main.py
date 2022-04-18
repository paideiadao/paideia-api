import uvicorn

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.users import users_router
from api.auth import auth_router
from core import config

app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url="/api/docs",
    openapi_url="/api"
)

#region Routers
app.include_router(users_router,      prefix="/api/users",      tags=["users"], dependencies=[Depends(get_current_active_user)])
app.include_router(auth_router,       prefix="/api/auth",       tags=["auth"])
#endregion Routers

# origins = ["*"]
origins = [
    "https://*.paideia.im",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# catch all route (useful?)
# @app.api_route("/{path_name:path}", methods=["GET"])
# async def catch_all(request: Request, path_name: str):
#     return {"request_method": request.method, "path_name": path_name}

@app.get("/api/ping")
async def ping():
    return {"hello": "world"}

# MAIN
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
