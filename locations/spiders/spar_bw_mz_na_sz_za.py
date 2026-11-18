from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES

BRANDS = {
    "SPAR": ("Spar", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "SUPERSPAR": ("Superspar", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_SUPERMARKET),
    "KWIKSPAR": ("KwikSpar", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_CONVENIENCE),
    "SPAR Express": ("Spar Express", SPAR_SHARED_ATTRIBUTES, Categories.SHOP_CONVENIENCE),
    "Savemor": ("SaveMor", {"brand": "SaveMor", "brand_wikidata": "Q610492"}, Categories.SHOP_SUPERMARKET),
}


class SparBWMZNASZZASpider(JSONBlobSpider):
    name = "spar_bw_mz_na_sz_za"
    skip_auto_cc_domain = True
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        for country in ["BW", "MZ", "NA", "SZ", "ZA"]:
            yield JsonRequest(url=f"https://www.spar.co.za/api/store-finder?country_code={country}&brands=SPAR")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        if item.get("addr_full") is not None:
            item["street_address"] = item.pop("addr_full")
        name, brand, category = BRANDS.get(feature["type"])
        if name:
            item["name"] = name

        if brand:
            item.update(brand)

        if category:
            apply_category(category, item)
        yield item
