from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SpeedeeUSSpider(AgileStoreLocatorSpider):
    name = "speedee_us"
    item_attributes = {"brand": "SpeeDee Oil Change and Auto Service", "brand_wikidata": "Q120537032"}
    allowed_domains = ["www.speedeeoil.com"]

    def parse_item(self, item, location):
        if " - #" in item["name"]:
            item["name"], item["ref"] = item["name"].split(" - #", 1)
        yield item
