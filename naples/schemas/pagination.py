from pydantic import BaseModel


class Params(BaseModel):
    page: int = 1
    size: int = 50

    def to_raw_params(self):
        return {
            "limit": self.size if self.size is not None else None,
            "offset": self.size * (self.page - 1) if self.page is not None and self.size is not None else None,
        }
