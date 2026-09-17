import re

from locations.storefinders.nomnom import NomNomSpider


class RedRobinSpider(NomNomSpider):
    name = "red_robin"
    item_attributes = {"brand": "Red Robin", "brand_wikidata": "Q7304886"}
    start_urls = ["https://www.redrobin.com/api/stores"]
    requires_proxy = True
    drop_attributes = {"name"}

    def post_process_item(self, item, response, feature):
        if re.search(r"\b(Lab|Demo)\b", feature["name"]):
            return  # NomNom test tenants ("Lab 4", "... Demo Vendor") with 555 phone numbers
        item["branch"] = feature["name"].removeprefix("Red Robin").strip()
        item["website"] = f"https://www.redrobin.com/location/{feature['slug']}"
        yield item
