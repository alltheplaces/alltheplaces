import re

from locations.storefinders.storepoint import StorepointSpider


class LaPorchettaSpider(StorepointSpider):
    name = "la_porchetta"
    item_attributes = {"brand": "La Porchetta", "brand_wikidata": "Q6464528"}
    key = "16156af5878536"

    def parse_item(self, item, location: {}, **kwargs):
        item["addr_full"] = item.pop("street_address")
        yield item
