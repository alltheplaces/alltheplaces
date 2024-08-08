import scrapy
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LibertyAUSpider(scrapy.Spider):
    name = "liberty_au"
    item_attributes = {"brand": "Liberty", "brand_wikidata": "Q106687078"}
    allowed_domains = ["libertyconvenience.com.au"]
    start_urls = ["https://www.libertyconvenience.com.au/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = location["store"]
            item["street_address"] = item.pop("addr_full", None)
            hours_string = " ".join(filter(None, Selector(text=location["hours"]).xpath("//text()").getall()))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            apply_category(Categories.FUEL_STATION, item)
            yield item
