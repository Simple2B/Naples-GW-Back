from fastapi import FastAPI

# import asyncio
# from contextlib import asynccontextmanager

from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination

from naples.config import config

from .utils import custom_generate_unique_id
from .routes import router

CFG = config()


api = FastAPI(version=CFG.VERSION, generate_unique_id_function=custom_generate_unique_id)
add_pagination(api)
api.include_router(router)

# TODO: second way to update data from stripe for user subscription
# async def update_data():
#     while True:
#         # TODO: add data update logic here
#         print("Updating data...")

#         days = CFG.DAYS_BEFORE_UPDATE
#         seconds_in_a_day = 24 * 60 * 60
#         total_seconds = days * seconds_in_a_day

#         # Wait for 3 days before the next update
#         await asyncio.sleep(total_seconds)


# @asynccontextmanager
# async def lifespan(api: FastAPI):
#     task = asyncio.create_task(update_data())
#     yield
#     task.cancel()
#     await task

# api.router.lifespan_context = lifespan


@api.get("/", tags=["root"])
async def root():
    return RedirectResponse(url="/docs")
