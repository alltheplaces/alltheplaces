from locations.storefinders.yext import YextSpider


class MatalanGBSpider(YextSpider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    api_key = "50f6010c48792a06524b4fe3471d7840"

    def parse_item(self, item, location):
        if not location.get("c_open_for_shopping"):
            return
        if not location["c_open_for_shopping"].get("availability"):
            return
        item["website"] = "https://store.matalan.co.uk/" + location["slug"]
        item.pop("twitter")
        yield item
