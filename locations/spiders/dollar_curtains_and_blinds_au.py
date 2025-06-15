from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DollarCurtainsAndBlindsAUSpider(Spider):
    name = "dollar_curtains_and_blinds_au"
    item_attributes = {"brand": "dollar curtains+blinds", "brand_wikidata": "Q122430680"}
    allowed_domains = ["www.dollarcurtainsandblinds.com.au"]
    start_urls = ["https://www.dollarcurtainsandblinds.com.au/app/themes/dcb-tailwind-2/cache/store-cache.json"]

    def parse(self, response):
        for location in response.json():
            location.update(location.pop("map_location"))
            item = DictParser.parse(location)
            item["ref"] = item["website"] = location["link"]
            item["addr_full"] = location["address_formatted"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["open_hours"])
            apply_category(Categories.SHOP_HOUSEWARE, item)
            yield item
