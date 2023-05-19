from locations.storefinders.yext import YextSpider


class ThreeGB(YextSpider):
    name = "three_gb"
    item_attributes = {"brand": "Three", "brand_wikidata": "Q407009"}
    api_key = "46281e259fc6522cc15ea1a0011c21a9"

    def parse_item(self, item, location):
        item["name"] = location["c_pageH1"]
        yield item
