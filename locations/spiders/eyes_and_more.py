import json
from urllib.parse import urljoin

from scrapy import Request, Selector, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.structured_data_spider import extract_phone


class EyesAndMoreSpider(Spider):
    name = "eyes_and_more"
    item_attributes = {"brand": "eyes + more", "brand_wikidata": "Q1385775"}
    start_urls = [
        "https://www.eyesandmore.be/nl/opticiens/",
        "https://www.eyesandmore.at/optiker/",
        "https://www.eyesandmore.de/optiker/",
        "https://www.eyesandmore.nl/opticiens/",
        # "https://www.eyesandmore.se/",  # 1 store, no store finder ATM
    ]

    def parse(self, response, **kwargs):
        for location in json.loads(response.xpath("//@data-locations").get()):
            item = DictParser.parse(location)

            selector = Selector(text=location["mapMarkerInfoWindowHTML"])
            item["addr_full"] = selector.xpath('//div[@class="address"]/text()').get()
            item["website"] = urljoin(response.url, selector.xpath('//a[@class="address-buttons__link"]/@href').get())
            extract_phone(item, selector)
            yield Request(url=item["website"], callback=self.parse_store, cb_kwargs={"item": item})

    def parse_store(self, response: Response, item: dict):
        for ld_data in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            for entry in json.loads(ld_data):
                if entry.get("@type") == "Store" and (specs := entry.get("openingHoursSpecification")):
                    item["opening_hours"] = OpeningHours()
                    for spec in specs:
                        item["opening_hours"].add_range(spec["dayOfWeek"], spec["opens"], spec["closes"])
        yield item
