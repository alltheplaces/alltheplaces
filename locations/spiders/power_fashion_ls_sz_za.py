from locations.storefinders.storepoint import StorepointSpider


class PowerFashionLSSZZASpider(StorepointSpider):
    name = "power_fashion_ls_sz_za"
    key = "162e1380619248"
    item_attributes = {"brand": "Power", "brand_wikidata": "Q118185713"}

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")
        yield item
