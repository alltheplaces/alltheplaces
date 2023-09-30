from locations.storefinders.metalocator import MetaLocatorSpider


class SpeedQueenSpider(MetaLocatorSpider):
    name = "speed_queen"
    item_attributes = {"brand": "Speed Queen", "brand_wikidata": "Q7575499"}
    brand_id = "15434"
    country_list = [
        "Albania",
        "Austria",
        "Azerbaijan",
        "Belgium",
        "Croatia",
        "Czech Republic",
        "Egypt",
        "France",
        "Georgia",
        "Germany",
        "Greece",
        "Hungary",
        "Ireland",
        "Italy",
        "Ivory Coast",
        "Kazakhstan",
        "Latvia",
        "Lithuania",
        "Netherlands",
        "Philippines",
        "Poland",
        "Portugal",
        "Slovenia",
        "Spain",
        "Ukraine",
        "United Kingdom",
        "US",
    ]

    def parse_item(self, item, location):
        item["ref"] = location["uniquekey"]
        yield item
