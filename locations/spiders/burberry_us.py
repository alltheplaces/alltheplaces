from locations.storefinders.uberall import UberallSpider


class BurberryUSSpider(UberallSpider):
    name = "burberry_us"
    item_attributes = {"brand": "Burberry", "brand_wikidata": "Q390107"}
    key = "wDs2IZte6mniM6J7TUaR3YI51ePyPa"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")

        yield item
