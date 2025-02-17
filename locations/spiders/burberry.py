from locations.storefinders.uberall import UberallSpider


class BurberrySpider(UberallSpider):
    name = "burberry"
    item_attributes = {"brand": "Burberry", "brand_wikidata": "Q390107"}
    # key = "wDs2IZte6mniM6J7TUaR3YI51ePyPa"
    key = "DrB2gWYxFo6Zjtq5m9w5uEjMOgh6Rg"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")

        yield item
