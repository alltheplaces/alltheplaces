from scrapy import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class GeniePointGBSpider(Spider):
    name = "genie_point_gb"
    item_attributes = {"operator": "GeniePoint", "operator_wikidata": "Q111363966"}
    start_urls = ["https://www.geniepoint.co.uk/ds/PublicMap/GetAllLocations"]

    def parse(self, response, **kwargs):
        for location in response.json()["rows"]:
            item = DictParser.parse(location)

            apply_yes_no(Extras.FEE, item, location["IsFreeCharge"], False)
            apply_category(Categories.CHARGING_STATION, item)
            yield item
