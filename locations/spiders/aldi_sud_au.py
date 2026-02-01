import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AldiSudAUSpider(UberallSpider):
    name = "aldi_sud_au"
    item_attributes = {"brand_wikidata": "Q41171672"}
    drop_attributes = {"name", "phone"}
    key = "Lbio8mFv9Ysxu1YhX4ARiQTNKOHNlE"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["website"] = "https://www.aldi.com.au/storelocator/l/{}/{}/{}".format(
            location["city"].lower().replace(" ", "-"),
            re.sub(
                r"-+", "-", location["streetAndNumber"].lower().replace("/", "-").replace(",", "-").replace(" ", "-")
            ),
            location["identifier"].lower(),
        )
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
