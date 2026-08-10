from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class BpPulseGBSpider(UberallSpider):
    name = "bp_pulse_gb"
    item_attributes = {"brand_wikidata": "Q39057719"}
    key = "Ngy4Zpj26HVGztRS6HikqkGY8AEUZ2"

    def post_process_item(self, item, response, location):
        item["name"] = item["phone"] = None
        apply_category(Categories.CHARGING_STATION, item)
        yield item
