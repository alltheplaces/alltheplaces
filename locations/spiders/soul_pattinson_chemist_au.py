from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SoulPattinsonChemistAUSpider(Spider):
    name = "soul_pattinson_chemist_au"
    item_attributes = {"brand": "Soul Pattinson Chemist", "brand_wikidata": "Q117225301"}
    start_urls = ["https://soulpattinson.com.au/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = location["store"].replace("&#038;", "&")
            item["street_address"] = item.pop("addr_full")
            hours = Selector(text=location["hours"])
            hours_string = " ".join(hours.xpath("//text()").getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
