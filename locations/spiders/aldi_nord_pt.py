from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class AldiNordPTSpider(UberallSpider):
    name = "aldi_nord_pt"
    item_attributes = {"brand_wikidata": "Q41171373"}
    key = "ALDINORDPT_YTvsWfhEG5TCPruM6ab6sZIi0Xodyx"

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name").removeprefix("ALDI ")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
