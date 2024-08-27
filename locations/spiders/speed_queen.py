from locations.storefinders.metalocator import MetaLocatorSpider


class SpeedQueenSpider(MetaLocatorSpider):
    name = "speed_queen"
    item_attributes = {"brand": "Speed Queen", "brand_wikidata": "Q7575499"}
    brand_id = "15434"

    def parse_item(self, item, location):
        item["ref"] = location["uniquekey"]
        yield item
