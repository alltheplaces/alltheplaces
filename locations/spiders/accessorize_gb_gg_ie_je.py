import re
from typing import Iterable

from scrapy.http import Response
from unidecode import unidecode

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AccessorizeGBGGIEJESpider(UberallSpider):
    name = "accessorize_gb_gg_ie_je"
    item_attributes = {"brand": "Accessorize", "brand_wikidata": "Q65007482"}
    key = "IivvWw4fta9V7tqZvojbvRfb5eIrO5"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        slug_city = re.sub(r"-+", "-", unidecode(re.sub(r"\W+", "-", item["city"].strip().lower())).replace(" ", "-"))
        slug_address = re.sub(
            r"-+", "-", unidecode(re.sub(r"\W+", "-", item["street_address"].strip().lower())).replace(" ", "-")
        )
        slug_id = str(location["id"])
        item["website"] = "https://www.accessorize.com/uk/stores/l/{}/{}/{}".format(slug_city, slug_address, slug_id)
        apply_category(Categories.SHOP_FASHION_ACCESSORIES, item)
        yield item
