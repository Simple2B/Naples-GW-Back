from fastapi import FastAPI


from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination

from naples.config import config

from .utils import custom_generate_unique_id
from .routes import router

CFG = config()


api = FastAPI(version=CFG.VERSION, generate_unique_id_function=custom_generate_unique_id)
add_pagination(api)
api.include_router(router)


@api.get("/", tags=["root"])
async def root():
    return RedirectResponse(url="/docs")
