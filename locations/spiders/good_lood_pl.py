from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GoodLoodPLSpider(Spider):
    name = "good_lood_pl"
    item_attributes = {"brand": "Good Lood", "brand_wikidata": "Q122978001"}
    start_urls = ["https://mobile.goodlood.com/loodspots"]

    def parse(self, response, **kwargs):
        for feature in response.json():
            if not feature["visible"]:
                continue
            item = DictParser.parse(feature)
            item["image"] = feature["image"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(feature["openingHours"])
            apply_yes_no(Extras.WHEELCHAIR, item, feature["facilities"]["ramp"])
            yield item
