from locations.storefinders.woosmap import WoosmapSpider


class UndizSpider(WoosmapSpider):
    name = "undiz"
    item_attributes = {"brand": "Undiz", "brand_wikidata": "Q105306275"}
    key = "woos-fb1b368e-2b65-3ead-a9f4-c3f62fa100b6"
    origin = "https://www.undiz.com"

    def parse_item(self, item, feature):
        item["branch"] = item.pop("name")
        yield item
