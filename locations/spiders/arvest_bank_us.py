from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.momentfeed import MomentFeedSpider


class ArvestBankUSSpider(MomentFeedSpider):
    name = "arvest_bank_us"
    item_attributes = {"brand": "Arvest Bank", "brand_wikidata": "Q4802393"}
    api_key = "RCKBBWJSPPOONTUT"

    def parse_item(self, item: Feature, feature: dict, store_info: dict):
        if "ATM" in item["name"]:
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
            if data := feature.get("tags"):
                apply_yes_no(Extras.ATM, item, True if "ATM" in data else False)
        yield item
