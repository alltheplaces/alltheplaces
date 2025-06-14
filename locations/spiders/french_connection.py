from locations.items import Feature
from locations.spiders.john_lewis_gb import JohnLewisGBSpider
from locations.spiders.tesco_gb import set_located_in
from locations.storefinders.storemapper import StoremapperSpider


class FrenchConnectionSpider(StoremapperSpider):
    name = "french_connection"
    item_attributes = {
        "brand_wikidata": "Q306457",
        "brand": "French Connection",
    }
    company_id = "11232"

    def parse_item(self, item: Feature, location: dict):
        item["branch"] = item.pop("name")
        if "John Lewis" in location["name"]:
            set_located_in(JohnLewisGBSpider.item_attributes, item)
        yield item
