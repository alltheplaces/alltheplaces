from locations.hours import DAYS_PT
from locations.spiders.lidl_at import LidlATSpider


class LidlPTSpider(LidlATSpider):
    name = "lidl_pt"

    dataset_id = "e470ca5678c5440aad7eecf431ff461a"
    dataset_name = "Filialdaten-PT/Filialdaten-PT"
    api_key = "Ahu0_AMpxF4eh7QlrRMfkhtrPnAKxYItqztODUDyRvuE4TzajeGVOxJSIZ6PUoR_"
    days = DAYS_PT
