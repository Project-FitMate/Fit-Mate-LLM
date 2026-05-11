from pydantic import BaseModel


class OutfitItem(BaseModel):
    image: str
    brand: str
    name: str
    price: int
    link: str
