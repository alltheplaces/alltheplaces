from locations.hours import DAYS_ES
from locations.spiders.lidl_at import LidlATSpider


class LidlLVSpider(LidlATSpider):
    name = "lidl_lv"

    dataset_id = "b2565f2cd7f64c759e2b5707b969e8dd"
    dataset_name = "Filialdaten-LV/Filialdaten-lv"
    api_key = "Ao9qjkbz2fsxw0EyySLTNvzuynLua7XKixA0yBEEGLeNmvrfkkb3XbfIs4fAyV-Z"
    days = DAYS_ES
