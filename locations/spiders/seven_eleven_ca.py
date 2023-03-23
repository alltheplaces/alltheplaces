from locations.categories import apply_yes_no, Extras
from locations.storefinders.yext import YextSpider


class SevenElevenCASpider(YextSpider):
    name = "seven_eleven_ca"
    item_attributes = {"brand": "7-Eleven", "brand_wikidata": "Q259340"}
    api_key = "4c8292a53c2dae5082ba012bdf783295"

    def parse_item(self, item, location):
        item.pop("twitter")
        if "c_delivery" in location:
            apply_yes_no(Extras.DELIVERY, item, location["c_delivery"], False)
        yield item
