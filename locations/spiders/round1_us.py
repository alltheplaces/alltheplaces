from locations.storefinders.storepoint import StorepointSpider


class Round1USSpider(StorepointSpider):
    name = "round1_us"
    item_attributes = {"brand": "Round1", "brand_wikidata": "Q11346634"}
    key = "16026f2c5ac3c7"

    def parse_item(self, item, location: {}, **kwargs):
        item["name"] = " ".join(item["name"].replace("<br>", "").split())
        yield item
