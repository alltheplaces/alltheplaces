from locations.storefinders.freshop import FreshopSpider


class PigglyWigglyUSSpider(FreshopSpider):
    name = "piggly_wiggly_us"
    item_attributes = {"brand": "Piggly Wiggly", "brand_wikidata": "Q3388303"}
    app_key = "piggly_wiggly_nc"

    def parse_item(self, item, location):
        item["phone"] = item["phone"].split("|", 1)[0].split("\n", 1)[0].strip()
        yield item
