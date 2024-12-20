import re

import scrapy
from chompjs import parse_js_object

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class VodafoneCZSpider(scrapy.Spider):
    name = "vodafone_cz"
    allowed_domains = ["www.vodafone.cz"]
    start_urls = ["https://www.vodafone.cz/prodejny/"]
    item_attributes = {
        "brand": "Vodafone",
        "brand_wikidata": "Q122141",
    }

    def extract_json(self, repsonse):
        js_blob = re.search(r"var stores = (.*)\n", repsonse.text)[1]
        return parse_js_object(js_blob)

    def parse(self, response):
        for location in self.extract_json(response):
            item = DictParser.parse(location)
            item["website"] = "https://www.vodafone.cz/prodejny/detail-prodejny/" + location["identifier"]
            apply_category(Categories.SHOP_MOBILE_PHONE, item)

            apply_yes_no(Extras.WHEELCHAIR_LIMITED, item, location["disabled_access"] == 2)
            apply_yes_no(Extras.WHEELCHAIR, item, location["disabled_access"] == 1)

            oh = OpeningHours()
            for key, values in location["opening_hours"].items():
                for value in values:
                    oh.add_range(value["day"], value["from"], value["till"])
            item["opening_hours"] = oh.as_opening_hours()
            yield item
