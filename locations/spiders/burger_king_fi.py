import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES

FEATURES_MAPPING = {
    "bk_delivery": Extras.DELIVERY,
    "drive_through": Extras.DRIVE_THROUGH,
    "take_away": Extras.TAKEAWAY,
}


class BurgerKingFISpider(scrapy.Spider):
    name = "burger_king_fi"
    allowed_domains = ["burgerking.fi"]
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.fi/wp-json/v2/restaurants"]

    def parse(self, response):
        for poi in response.json():
            poi["street_address"] = poi.pop("address")
            item = DictParser.parse(poi)
            item["ref"] = item["name"]
            # 'features' might be an empty list or filled dict
            if features := poi.get("features"):
                for feature, value in features.items():
                    if tags := FEATURES_MAPPING.get(feature):
                        apply_yes_no(tags, item, value, True)
            # TODO: parse opening hours
            yield item
