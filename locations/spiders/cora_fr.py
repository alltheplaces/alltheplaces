from locations.storefinders.woosmap import WoosmapSpider


class CoraFRSpider(WoosmapSpider):
    name = "cora_fr"
    item_attributes = {"brand": "Cora", "brand_wikidata": "Q686643"}
    key = "woos-789d2f65-5cee-39a3-9e38-a31bd63a6b57"
    origin = "https://www.cora.fr"

    def parse_item(self, item, feature, **kwargs):
        # Filter only on CORA shop and not affiliated shop
        if not item["name"].startswith("CORA"):
            return
        item["website"] = "https://www.cora.fr" + item["website"]
        yield item
