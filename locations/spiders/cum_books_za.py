from chompjs import parse_js_object
from scrapy import Spider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CumBooksZASpider(Spider):
    name = "cum_books_za"
    item_attributes = {
        "brand_wikidata": "Q128930625",
        "brand": "CUM Books",
    }
    allowed_domains = ["storage.googleapis.com"]
    start_urls = ["https://storage.googleapis.com/maps-solutions-5awgpybsml/locator-plus/k456/locator-plus-config.js"]
    no_refs = True

    def parse(self, response):
        js_blob = "[" + response.text.split('"locations": [', 1)[1].split("],", 1)[0] + "]"
        locations = parse_js_object(js_blob)

        for location in locations:
            properties = {
                "branch": location["title"].replace("CUM Books - ", ""),
                "lat": location["coords"]["lat"],
                "lon": location["coords"]["lng"],
                "street_address": location["address1"],
                "addr_full": clean_address([location["address1"], location["address2"]]),
                "extras": {"ref:google": location.get("placeId")},
            }

            yield Feature(**properties)
