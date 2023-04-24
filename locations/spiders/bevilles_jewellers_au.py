from locations.storefinders.storemapper import StoremapperSpider


class BevillesJewellersAUSpider(StoremapperSpider):
    name = "bevilles_jewellers_au"
    item_attributes = {"brand": "Bevilles Jewellers", "brand_wikidata": "Q117837188"}
    key = "6228"

    def parse_item(self, item, location):
        item["name"] = item["name"].replace("Bevilles Jewellers | ", "")
        yield item
