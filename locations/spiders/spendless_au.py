import re

from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class SpendlessAUSpider(Spider):
    name = "spendless_au"
    item_attributes = {"brand": "Spendless", "brand_wikidata": "Q120668938"}
    allowed_domains = ["www.spendless.com.au"]
    start_urls = ["https://www.spendless.com.au/stockists/index/search/"]

    def start_requests(self):
        for url in self.start_urls:
            formdata = {
                "key": "AIzaSyBBmCV6MpgFqu7dq9ummJrwbXsD5OeCOdU",
                "components[country]": "AU",
                "radius": "50000",
                "units": "km",
                "page": "0",
                "address": "0870",
            }
            headers = {
                "X-Requested-With": "XMLHttpRequest",
            }
            yield FormRequest(url=url, formdata=formdata, headers=headers, method="POST")

    def parse(self, response):
        for location in response.json()["results"]["results"]:
            if "OPENING SOON" in location["street"].upper() or "ONLINE STORE" in location["name"].upper():
                continue
            item = DictParser.parse(location)
            item["ref"] = location["identifier"]
            item.pop("street")
            item["street_address"] = clean_address([location.get("street"), location.get("street2")])
            hours_string = re.sub(r"\s+", " ", location.get("opening_hours", "")).strip()
            if hours_string:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
