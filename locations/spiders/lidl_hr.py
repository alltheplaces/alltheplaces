from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlHRSpider(VirtualEarthSpider):
    name = "lidl_hr"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "d82c19ca83104facab354f376bf4312b"
    dataset_name = "Filialdaten-HR/Filialdaten-HR"
    api_key = "AoX_2ZTHnC3kIskrKATT7ZcheF4L7vHMCaHTqcTpjmaOm3kIGwASRnEqLpeH7_-S"
