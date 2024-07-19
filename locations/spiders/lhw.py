import json

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS

FEATURES_MAPPING = {
    "Swimming Pool(s)": Extras.SWIMMING_POOL,
    "Pet Friendly - Conditions Apply": Extras.PETS_ALLOWED,
    # TODO: other features
}


class LhwSpider(scrapy.Spider):
    name = "lhw"
    allowed_domains = ["www.lhw.com"]
    start_urls = ["https://www.lhw.com/services/json/FindAllHotelsV2_en.js"]
    item_attributes = {"brand": "The Leading Hotels of the World", "brand_wikidata": "Q834396"}
    is_playwright_spider = True
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        **DEFAULT_PLAYWRIGHT_SETTINGS,
    }

    def parse(self, response):
        json_data = json.loads(response.xpath("//pre/text()").get())
        pois = json_data["d"]["Hotels"]
        for poi in pois:
            item = DictParser.parse(poi)
            item.pop("street_address")
            item["addr_full"] = (
                poi.get("Address1")
                if not poi.get("Address2")
                else ", ".join([poi.get("Address1"), poi.get("Address2")])
            )
            item["ref"] = poi["BookingNumber"]
            item["image"] = poi["Image"]
            item["website"] = poi["Link"]
            apply_category(Categories.HOTEL, item)
            self.parse_features(item, poi)
            yield item

    def parse_features(self, item, poi):
        for feature in poi.get("Features", []):
            if tag := FEATURES_MAPPING.get(feature):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"lhw/feature_not_mapped/{feature}")
