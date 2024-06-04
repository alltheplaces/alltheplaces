from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MisterMinitAsiaPacificSpider(Spider):
    name = "mister_minit_asia_pacific"
    item_attributes = {"brand": "Mister Minit", "brand_wikidata": "Q1939269", "extras": Categories.SHOP_LOCKSMITH.value}
    allowed_domains = ["storage.googleapis.com"]
    start_urls = ["https://storage.googleapis.com/maps-solutions-7ge5m84jyd/locator-plus/08n0/locator-plus-config.js"]
    no_refs = True

    def parse(self, response):
        js_blob = "[" + response.text.split('"locations": [', 1)[1].split("],", 1)[0] + "]"
        locations = parse_js_object(js_blob)

        for location in locations:
            properties = {
                "name": location["title"],
                "lat": location["coords"]["lat"],
                "lon": location["coords"]["lng"],
                "street_address": location["address1"],
                "addr_full": clean_address([location["address1"], location["address2"]]),
                "extras": {"ref:google": location.get("placeId")},
            }

            if location["address2"].endswith("Australia"):
                properties["country"] = "AU"
            elif location["address2"].endswith("New Zealand"):
                properties["country"] = "NZ"
            elif location["address2"].endswith("Singapore"):
                properties["country"] = "SG"
            elif location["address2"].endswith("Malaysia"):
                properties["country"] = "MY"
            else:
                self.logger.warning(
                    "Feature located in country that is not currently known to this spider. Address including country: {}".format(
                        location["address2"]
                    )
                )

            yield Feature(**properties)
