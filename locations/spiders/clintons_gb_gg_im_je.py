from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class ClintonsGBGGIMJESpider(JSONBlobSpider):
    name = "clintons_gb_gg_im_je"
    item_attributes = {"brand": "Clintons", "brand_wikidata": "Q5134299"}
    start_urls = ["https://clintonscards.co.uk/wp-json/store-locations/v1/search"]
    drop_attributes = {"facebook", "twitter", "email"}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([item.pop("addr_full"), feature["address2"]])
        item["branch"] = item.pop("name", None)
        item["country"] = "GB"
        item["ref"] = feature["link"]
        if item.get("phone") and not item["phone"].startswith("+44"):
            item["phone"] = "+44 " + item["phone"]

        apply_category(Categories.SHOP_GIFT, item)

        yield item
