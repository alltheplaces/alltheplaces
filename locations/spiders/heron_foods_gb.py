from typing import Iterable

from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.storefinders.wordpress_heron_foods_spider import WordpressHeronFoodsSpider

B_AND_M_EXPRESS = {"brand": "B&M Express", "brand_wikidata": "Q99640578"}


class HeronFoodsGBSpider(WordpressHeronFoodsSpider):
    name = "heron_foods_gb"
    item_attributes = {"brand": "Heron Foods", "brand_wikidata": "Q5743472"}
    domain = "heronfoods.com"
    radius = 600
    lat = 51.5072178
    lon = -0.1275862

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:

        if item["website"].endswith("-bm-express/"):
            item["branch"] = item["branch"].replace("B&M Express", "").removesuffix(" ()")
            item.update(B_AND_M_EXPRESS)

        features = [f for f in feature["fi"].values()]

        apply_yes_no(Extras.ATM, item, "ATM" in features)
        apply_yes_no("sells:alcohol", item, "Alcohol" in features)
        apply_yes_no(Extras.DELIVERY, item, "Home Delivery" in features)
        apply_yes_no("sells:lottery", item, "National Lottery" in features)
        apply_yes_no("paypoint", item, "PayPoint" in features)

        yield item
