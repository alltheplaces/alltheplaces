from locations.storefinders.uberall import UberallSpider


class BurberryUSSpider(UberallSpider):
    name = "burberry_us"
    item_attributes = {"brand": "Burberry", "brand_wikidata": "Q390107"}
    key = "wDs2IZte6mniM6J7TUaR3YI51ePyPa"

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name")

        yield item
