from pydantic import BaseModel, Field, AliasChoices


class EditableText(BaseModel):
    value: str
    color: str
    font_size: int = Field(..., validation_alias=AliasChoices("font_size", "fontSize"), serialization_alias="fontSize")
