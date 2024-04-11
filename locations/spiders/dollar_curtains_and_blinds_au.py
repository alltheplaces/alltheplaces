from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DollarCurtainsAndBlindsAUSpider(Spider):
    name = "dollar_curtains_and_blinds_au"
    item_attributes = {"brand": "dollar curtains+blinds", "brand_wikidata": "Q122430680"}
    allowed_domains = ["www.dollarcurtainsandblinds.com.au"]
    start_urls = ["https://www.dollarcurtainsandblinds.com.au/app/themes/dcb-tailwind-2/cache/store-cache.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["link"]
            item["name"] = location["map_location"]["name"]
            item["lat"] = location["map_location"]["lat"]
            item["lon"] = location["map_location"]["lng"]
            item["addr_full"] = location["address_formatted"]
            item["housenumber"] = location["map_location"]["street_number"]
            item["street"] = location["map_location"]["street_name"]
            item["city"] = location["map_location"]["city"]
            item["state"] = location["map_location"]["state"]
            item["postcode"] = location["map_location"]["post_code"]
            item["country"] = location["map_location"]["country"]
            item["website"] = location["link"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["open_hours"])
            apply_category(Categories.SHOP_HOUSEWARE, item)
            yield item
