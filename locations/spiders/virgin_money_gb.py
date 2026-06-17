from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.woosmap import WoosmapSpider


class VirginMoneyGBSpider(WoosmapSpider):
    name = "virgin_money_gb"
    item_attributes = {
        "brand_wikidata": "Q2527746",
        "brand": "Virgin Money",
    }
    key = "woos-89a9a4a8-799f-3cbf-9917-4e7b88e46c30"
    origin = "https://uk.virginmoney.com"

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name")
        apply_category(Categories.BANK, item)

        tags = feature["properties"].get("tags", [])
        apply_yes_no(Extras.ATM, item, "atm" in tags)
        apply_yes_no(Extras.WIFI, item, "free_wifi" in tags)
        apply_yes_no(Extras.WHEELCHAIR, item, "disabled_access" in tags)
        apply_yes_no(Extras.CASH_IN, item, "deposit_atm" in tags)
        apply_yes_no("speech_output", item, "audio_atm" in tags)

        yield item
