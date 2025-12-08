from locations.hours import DAYS_IT
from locations.spiders.lidl_at import LidlATSpider


class LidlITSpider(LidlATSpider):
    name = "lidl_it"

    dataset_id = "a360ccf2bf8c442da306b6eb56c638d7"
    dataset_name = "Filialdaten-IT/Filialdaten-IT"
    api_key = "AotMQpa96W8m5_F4ayN9WYBaEQLlxtI3ma8VpOWubmVHTOdZmmKoXjZ8IGLnratj"
    days = DAYS_IT
