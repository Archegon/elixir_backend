from fastapi import FastAPI
from api.http_routes import router as http_router
from api.websocket_routes import router as ws_router

app = FastAPI()

app.include_router(http_router)
app.include_router(ws_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
