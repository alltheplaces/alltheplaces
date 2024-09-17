from locations.storefinders.storemapper import StoremapperSpider


class BarrysSpider(StoremapperSpider):
    name = "barrys"
    item_attributes = {
        "brand_wikidata": "Q96373178",
        "brand": "Barry's",
    }
    company_id = "5809"

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")
        yield item
