from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class CityBeachAUSpider(Spider):
    name = "city_beach_au"
    item_attributes = {"brand": "City Beach", "brand_wikidata": "Q16958619", "extras": Categories.SHOP_CLOTHES.value}
    allowed_domains = ["www.citybeach.com"]
    start_urls = [
        "https://www.citybeach.com/on/demandware.store/Sites-CityBeachAustralia-Site/default/Stores-FindStores?showMap=true&radius=10000&postalCode=0870"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            if branch_name := item.pop("name", None):
                item["branch"] = branch_name
            item.pop("addr_full", None)
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["storeHours"].replace("<br>", " "))
            yield item
