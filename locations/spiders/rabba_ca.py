from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class RabbaCASpider(Spider):
    name = "rabba_ca"
    item_attributes = {"brand": "Rabba", "brand_wikidata": "Q109659398", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["core.service.elfsight.com"]
    start_urls = [
        "https://core.service.elfsight.com/p/boot/?page=https://rabba.com/locations/&w=3df8be4a-1f05-46f7-86b4-f9dd7e4f717a"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]["widgets"]["3df8be4a-1f05-46f7-86b4-f9dd7e4f717a"]["data"]["settings"][
            "markers"
        ]:
            item = DictParser.parse(location)
            item["name"] = location.get("infoTitle")
            item["lat"], item["lon"] = location.get("coordinates").split(", ", 1)
            item["addr_full"] = location.get("infoAddress")
            item["phone"] = location.get("infoPhone")
            item["email"] = location.get("infoEmail")
            item["website"] = location.get("linkUrl")
            if "24 HOURS" in location.get("infoWorkingHours").upper():
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            yield item
