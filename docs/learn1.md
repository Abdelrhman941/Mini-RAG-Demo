```
├── assets
│   ├── .gitkeep                  # to keep the empty directory in git
│   └── Mini-RAG.json
├── src
│   ├── core
│   │   └── configs.py            # Application configuration using Pydantic
│   ├── routes
│   │   ├── __init__.py
│   │   └── base.py               # Base route for the application
│   └── main.py
├── .env.example
├── README.md
└── requirements.txt
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **configs.py**
```py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Mini-RAG"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "A mini RAG application for demo purposes."

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()
```

#### **Configuration Loading Priority** -> **Config class**: Tells Pydantic to load environment variables from the `.env` file.

The priority order for loading configuration values is:

```
1️⃣ Environment variables
   └── Set directly in the system environment
   └── Takes highest precedence

2️⃣ `.env` file values
   └── Loaded from the `.env` file if present
   └── Applied only if not set in environment

3️⃣ Default values
   └── Defined in the `Settings` class (in `configs.py`)
   └── Used when no value is provided from higher sources
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **base.py**
```py
from fastapi import APIRouter, Depends
from core.configs import Settings, get_settings

base_router = APIRouter(
    prefix="/v1",               # to put all routes under /v1
    tags=["Base"],              # for API documentation grouping `you can see it swagger UI`
)


@base_router.get("/")
async def read_root(appsSettings: Settings = Depends(get_settings)):
    return {
        "APP": appsSettings.APP_NAME,
        "VERSION": appsSettings.APP_VERSION,
        "DESCRIPTION": appsSettings.APP_DESCRIPTION,
    }
```

```
`appsSettings: Settings = Depends(get_settings)`
  │                │          │       │
  │                │          │       └── The function that retrieves Settings ->> (defined in configs.py)
  │                │          └── FastAPI's Dependency Injection tool "Tell FastAPI to call this function and pass its result here"
  │                └── Expected data type -------------------------------------->> (defined in configs.py)
  └── Variable name we'll use
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **main.py**
```py
from fastapi import FastAPI
from routes import base         # routes folder which contains base.py with the base_router

app = FastAPI()

app.include_router(base.base_router)
```
