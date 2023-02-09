from locations.storefinders.storepoint import StorepointSpider


class ZarraffasCoffeeAUSpider(StorepointSpider):
    name = "zarraffas_coffee_au"
    item_attributes = {"brand": "Zarraffa's Coffee", "brand_wikidata": "Q8066878"}
    key = "15cc7dc6818a9c"

    def parse_item(self, item, location: {}, **kwargs):
        if item["website"] is not None:
            item["website"] = "https://zarraffas.com" + item["website"]
        yield item
