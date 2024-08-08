import re

from locations.categories import Categories, apply_category
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class DuskNZSpider(AmastyStoreLocatorSpider):
    name = "dusk_nz"
    item_attributes = {"brand": "dusk", "brand_wikidata": "Q120669167"}
    allowed_domains = ["www.duskcandles.co.nz"]

    def parse_item(self, item, location, popup_html):
        address_string = re.sub(r"\s+", " ", " ".join(filter(None, popup_html.xpath("//text()").getall())))
        item["city"] = address_string.split("City: ", 1)[1].split(" Postcode: ", 1)[0]
        item["postcode"] = address_string.split("Postcode: ", 1)[1].split(" Address: ", 1)[0]
        item["street_address"] = address_string.split("Address: ", 1)[1].split(" Region: ", 1)[0]
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
