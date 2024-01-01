from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CampingWorldAUSpider(Spider):
    name = "camping_world_au"
    item_attributes = {"brand": "Camping World", "brand_wikidata": "Q124062618"}
    allowed_domains = ["www.campingworld.com.au"]
    start_urls = ["https://www.campingworld.com.au/index.php?hcs=locatoraid&hcrand=3018&hca=search:search//product/_PRODUCT_/lat//lng//limit/1000"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, headers={"X-Requested-With": "XMLHttpRequest"})

    def parse(self, response):
        for location in response.json()["results"]:
            item = DictParser.parse(location)
            item.pop("addr_full", None)
            item["street_address"] = ", ".join(filter(None, [location.get("street1"), location.get("street2")]))
            item["phone"] = Selector(text=location.get("phone")).xpath('//a[contains(@href, "tel:")]/@href').get().replace("tel:", "")
            item["email"] = Selector(text=location.get("misc1")).xpath('//a[contains(@href, "mailto:")]/@href').get().replace("mailto:", "")
            hours_string = " ".join(Selector(text=location.get("misc3")).xpath('//text()').getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
