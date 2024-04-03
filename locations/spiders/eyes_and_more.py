import json
from urllib.parse import urljoin

from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, DAYS_NL, OpeningHours, sanitise_day
from locations.structured_data_spider import extract_phone


class EyesAndMoreDESpider(Spider):
    name = "eyes_and_more"
    item_attributes = {"brand": "eyes + more", "brand_wikidata": "Q1385775"}
    start_urls = [
        "https://www.eyesandmore.be/nl/opticiens/",
        "https://www.eyesandmore.at/optiker/",
        "https://www.eyesandmore.de/optiker/",
        "https://www.eyesandmore.nl/opticiens/",
        # "https://www.eyesandmore.se/",  # 1 store, no store finer ATM
    ]
    DAYS = DAYS_NL | DAYS_DE

    def parse(self, response, **kwargs):
        for location in json.loads(response.xpath("//@data-locations").get()):
            item = DictParser.parse(location)

            selector = Selector(text=location["infoWindowHtml"])
            item["addr_full"] = selector.xpath('//div[@class="address"]/text()').get()
            item["website"] = urljoin(response.url, selector.xpath('//a[@class="button"]/@href').get())
            extract_phone(item, selector)

            item["opening_hours"] = OpeningHours()
            for rule in location["formatDetails"]["openingTimes"]:
                if day := sanitise_day(rule["label"], self.DAYS):
                    if times := rule["times"]:
                        if times in ["Geschlossen", "Gesloten"]:
                            continue
                        start_time, end_time = times.split(" - ")
                        item["opening_hours"].add_range(day, start_time, end_time)

            yield item
