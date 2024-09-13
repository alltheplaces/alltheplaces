from locations.hours import DAYS_CZ
from locations.spiders.lidl_at import LidlATSpider


class LidlCZSpider(LidlATSpider):
    name = "lidl_cz"

    dataset_id = "f6c4e6f3d86d464088f7a6db1598538e"
    dataset_name = "Filialdaten-CZ/Filialdaten-CZ"
    api_key = "AiNNY2F5r0vNd6fJFLwr-rT5fPEDBzibjcQ0KMyUalKrIqaoM8HUlNAMEFFkBEv-"
    days = DAYS_CZ
