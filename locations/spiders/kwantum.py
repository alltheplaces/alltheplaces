from urllib.parse import urlparse

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class KwantumSpider(Spider):
    name = "kwantum"
    item_attributes = {"brand": "Kwantum", "brand_wikidata": "Q2262591"}
    start_urls = ["https://www.kwantum.be/api/nl-BE/stores", "https://www.kwantum.nl/api/nl-NL/stores"]

    def parse(self, response, **kwargs):
        base_domain = urlparse(response.url).netloc
        for location in response.json():
            location["data"]["location"] = location.pop("position")
            location["data"]["ref"] = location.pop("id")
            location["data"]["street_address"] = location["data"].pop("address")
            location["data"]["website"] = f'https://{base_domain}{location["data"]["href"]}'
            item = DictParser.parse(location["data"])

            item["opening_hours"] = OpeningHours()
            for rule in location["data"]["openingHours"]:
                if day := sanitise_day(rule["label"], DAYS_NL):
                    times = rule["displayValue"]
                    if times == "Gesloten":
                        continue
                    start_time, end_time = times.split("-")
                    item["opening_hours"].add_range(day, start_time, end_time)

            yield item
