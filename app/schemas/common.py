from enum import Enum


class OutfitPart(str, Enum):
    FULL = "FULL"
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    OUTER = "OUTER"
    DRESS = "DRESS"
    SHOES = "SHOES"
    HAT = "HAT"


class MimeType(str, Enum):
    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"
