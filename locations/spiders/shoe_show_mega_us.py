import re
from typing import Iterable

import scrapy
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

BRANDS = {
    "SHOE SHOW MEGA STORE ": {"brand": "Shoe Show Mega", "brand_wikidata": "Q7500015"},
    "Burlington Shoes ": {"brand": "Burlington Shoes"},
    "SHOE DEPT. ENCORE ": {"brand": "Shoe Dept. Encore", "brand_wikidata": "Q128119319"},
    "SHOE DEPT. ": {"brand": "Shoe Dept.", "brand_wikidata": "Q128119319"},
    "SHOE SHOW ": {"brand": "Shoe Show", "brand_wikidata": "Q7500015"},
}


class ShoeShowMegaUSSpider(JSONBlobSpider):
    name = "shoe_show_mega_us"
    custom_settings = {"ROBOTSTXT_OBEY": "False"}
    locations_key = "stores"

    def start_requests(self) -> Iterable[JsonRequest | Request]:
        for index, record in enumerate(postal_regions("US")):
            if index % 100 == 0:
                yield scrapy.Request(
                    url=f'https://www.shoeshowmega.com/on/demandware.store/Sites-shoe-show-Site/default/Stores-FindStores?showMap=true&radius=200&radio=false&postalCode={record["postal_region"]}'
                )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([item["street_address"], feature["address2"]])

        for prefix, brand in BRANDS.items():
            if item["name"].startswith(prefix):
                item.update(brand)
                break
        else:
            self.logger.error("Unexpected brand: {}".format(item["name"]))

        item["opening_hours"] = OpeningHours()
        for rule in re.findall(r"(?si)([a-z]+)\s*(\d+:\d+.M)\s*-\s*(\d+:\d+.M)", feature["storeHours"]):
            item["opening_hours"].add_range(rule[0], rule[1], rule[2], "%I:%M%p")

        apply_category(Categories.SHOP_SHOES, item)
        yield item
