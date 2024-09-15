from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WinmartVNSpider(JSONBlobSpider):
    name = "winmart_vn"
    allowed_domains = ["api-crownx.winmart.vn"]
    start_urls = ["https://api-crownx.winmart.vn/mt/api/web/v1/store-by-province?pageSize=1000"]
    locations_key = "data"

    def parse(self, response: Response) -> Iterable[Feature]:
        features = self.extract_json(response)
        for district in features:
            for ward in district["wardStores"]:
                yield from self.parse_feature_array(response, ward["stores"])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["chainId"] == "VMT":
            item["brand"] = "WinMart"
            item["brand_wikidata"] = "Q60245505"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif feature["chainId"] == "VMP":
            item["brand"] = "WinMart+"
            item["brand_wikidata"] = "Q113236478"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            raise ValueError("Unknown brand detected: {}".format(feature["chainId"]))

        item["branch"] = item.pop("name", "").removeprefix("WM ").removeprefix("WM+ ").removeprefix("{} ".format(feature.get("provinceCode", "")))
        item["addr_full"] = feature.get("officeAddress")
        item["state"] = feature.get("provinceCode")
        item["city"] = feature.get("wardName").removeprefix("P. ").removeprefix("TT. ").removeprefix("X. ")
        item["phone"] = feature.get("contactMobile")

        yield item

