from fastapi import Request, HTTPException


async def get_body(request: Request):
    content_type = request.headers.get("Content-Type")
    if content_type is None:
        raise HTTPException(status_code=400, detail="No Content-Type provided!")
    elif content_type == "application/x-www-form-urlencoded" or content_type.startswith("multipart/form-data"):
        try:
            return await request.form()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Form data")
    else:
        raise HTTPException(status_code=400, detail="Content-Type not supported!")
