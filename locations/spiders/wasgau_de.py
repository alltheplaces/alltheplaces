from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours


class WasgauDESpider(Spider):
    name = "wasgau_de"
    item_attributes = {"brand": "Wasgau", "brand_wikidata": "Q2536857"}
    allowed_domains = ["www.wasgau.de"]
    start_urls = ["https://www.wasgau.de/app/uploads/maerkte.json?123"]

    def parse(self, response):
        for location in response.json():
            # Response is well formed GeoJSON
            properties = location["properties"]
            item = DictParser.parse(properties)
            item["geometry"] = location["geometry"]
            item["ref"] = (
                item["name"] + item["street"] + item["postcode"]
            )  # No ids, so this is the best unique key I can find
            item["website"] = properties["post_link"]

            if properties["markt_typ"] == "mini":
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif properties["markt_typ"] == "himmelherd":
                # Brand is Himmel und Herd, restaurant? Diner? Hard to determine
                apply_category(Categories.RESTAURANT, item)
            elif properties["markt_typ"] == "frischemarkt":
                apply_category(
                    Categories.SHOP_SUPERMARKET, item
                )  # TODO: Check if "Fresh market" (food, flowers, etc) is closest to supermarket
            elif properties["markt_typ"] == "bakery":
                apply_category(Categories.SHOP_BAKERY, item)

            if "oeffnungszeiten" in properties:
                item["opening_hours"] = OpeningHours()
                for hours in properties["oeffnungszeiten"]:
                    item["opening_hours"].add_range(DAYS_DE[hours["day"]], hours["opens"], hours["closes"], "%H:%M")
            yield item
