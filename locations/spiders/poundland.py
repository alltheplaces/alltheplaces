from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider


class PoundlandSpider(WoosmapSpider):
    name = "poundland"
    item_attributes = {"brand": "Poundland", "brand_wikidata": "Q1434528"}
    key = "woos-4108db5c-39f8-360b-9b7e-102c38034b94"
    origin = "https://www.poundland.co.uk"

    def parse_item(self, item: Feature, feature: dict, **kwargs):
        item["branch"] = item.pop("name")

        if "Pep Shop" in feature["properties"]["tags"] or item["branch"].startswith("Pep & Co "):
            pep = item.deepcopy()

            pep["ref"] = pep["ref"] + "_pep"

            pep["brand"] = "Pep&Co"
            pep["brand_wikidata"] = "Q24908166"

            pep["located_in"] = self.item_attributes["brand"]
            pep["located_in_wikidata"] = self.item_attributes["brand_wikidata"]

            yield pep

        if item["branch"].startswith("Pep & Co "):
            return

        apply_yes_no(Extras.ATM, item, "ATM" in feature["properties"]["tags"])
        item["extras"]["icestore"] = "yes" if "Ice Store" in feature["properties"]["tags"] else "no"

        yield item
