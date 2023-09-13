import re

from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class PetrolBGSpider(AgileStoreLocatorSpider):
    name = "petrol_bg"
    item_attributes = {"brand": "Petrol", "brand_wikidata": "Q24315"}
    allowed_domains = ["www.petrol.bg"]

    def parse_item(self, item, location):
        if m := re.match(r"^(\d+) (.+)$", item["name"]):
            item["ref"] = m.group(1)
            item["name"] = m.group(2)
        yield item
