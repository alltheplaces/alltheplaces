import re

from locations.categories import apply_category
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class DuskAUSpider(AmastyStoreLocatorSpider):
    name = "dusk_au"
    item_attributes = {"brand": "dusk", "brand_wikidata": "Q120669167"}
    allowed_domains = ["www.dusk.com.au"]

    def parse_item(self, item, location, popup_html):
        address_string = re.sub(r"\s+", " ", " ".join(filter(None, popup_html.xpath("//text()").getall())))
        item["city"] = address_string.split("City: ", 1)[1].split(" Zip: ", 1)[0]
        item["postcode"] = address_string.split("Zip: ", 1)[1].split(" Address: ", 1)[0]
        item["street_address"] = address_string.split("Address: ", 1)[1].split(" State: ", 1)[0]
        item["state"] = address_string.split("State: ", 1)[1].split(" Description: ", 1)[0]
        apply_category({"shop": "houseware"}, item)
        yield item
