from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser


class HarcourtsSpider(Spider):
    name = "harcourts"
    item_attributes = {"brand": "Harcourts", "brand_wikidata": "Q5655056"}
    allowed_domains = ["harcourts.net"]
    start_urls = [
        "https://harcourts.net/nz/offices",
        "https://harcourts.net/au/offices",
        "https://harcourts.net/fj/offices",
    ]

    def parse(self, response):
        locations_js = (
            response.xpath('//script[contains(text(), "var mapItemSearchResultsJSON = ")]/text()')
            .get()
            .split("var mapItemSearchResultsJSON = ", 1)[1]
            .split("}];", 1)[0]
            + "}]"
        )
        for location in parse_js_object(locations_js):
            item = DictParser.parse(location)
            if "/nz/" in response.url:
                item["country"] = "NZ"
            elif "/au/" in response.url:
                item["country"] = "AU"
            elif "/fj/" in response.url:
                item["country"] = "FJ"
            item["ref"] = "https://harcourts.net" + location["url"]
            item["website"] = "https://harcourts.net" + location["url"]
            yield item
