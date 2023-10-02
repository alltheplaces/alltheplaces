from chompjs import parse_js_object
from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KiKSpider(Spider):
    name = "kik"
    item_attributes = {"brand": "KiK", "brand_wikidata": "Q883965"}
    allowed_domains = ["www.kik.de", "storefinder-microservice.kik.de"]
    start_urls = ["https://www.kik.de/storefinderAssets/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_country_list)

    def parse_country_list(self, response):
        country_list_js = (
            response.xpath('//script[contains(text(), "const translations = {")]/text()')
            .get()
            .split("countries:", 1)[1]
            .split("},", 1)[0]
            + "}"
        )
        for country_code in parse_js_object(country_list_js).keys():
            # Whilst it is possible to omit the country code to return all
            # locations globally, the resulting data does not provide a
            # country field or other means besides reverse geocoding to
            # determine the country of each location. Thus it is easier to
            # filter by country and pass the country code to
            # self.parse_stores to add the country code field.
            yield JsonRequest(
                url=f"https://storefinder-microservice.kik.de/storefinder/results.json?lat=&long=&country={country_code}&distance=100000&limit=100000",
                meta={"country_code": country_code},
                callback=self.parse_stores,
            )

    def parse_stores(self, response):
        for location in response.json()["stores"][0]["results"].values():
            item = DictParser.parse(location)
            item["ref"] = location["filiale"]
            item["street_address"] = item.pop("addr_full", None)
            item["country"] = response.meta["country_code"].upper()
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["opening_times"], delimiters=["-", "*"])
            yield item
