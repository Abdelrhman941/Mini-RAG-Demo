from fastapi import FastAPI
from routes import base

app = FastAPI()

app.include_router(base.base_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
