from locations.storefinders.kibo import KiboSpider
from locations.user_agents import BROWSER_DEFAULT


class FrancescasUSSpider(KiboSpider):
    name = "francescas_us"
    item_attributes = {"brand": "Francesca's", "brand_wikidata": "Q72982331"}
    start_urls = ["https://www.francescas.com/api/commerce/storefront/locationUsageTypes/SP/locations"]
    user_agent = BROWSER_DEFAULT

    def parse_item(self, item, location: {}, **kwargs):
        for attribute in location["attributes"]:
            if attribute["fullyQualifiedName"] == "tenant~store url":
                item["website"] = (
                    "https://www.francescas.com/store-details/" + item["ref"] + "/" + attribute["values"][0]
                )
        yield item
