from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_yes_no
from locations.geo import country_iseadgg_centroids
from locations.items import Feature, merge_items
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address

FEATURE_MAPPING = {
    # "BE"  # Barista-Crafted Reserve Beverages
    "DL": Extras.DELIVERY,
    # "MIC"  # Starbucks Ice Cream Plus
    # "MOP"  # Mobile order and pickup
    # "NCB"  # Nitro Cold Brew
    # "OG"  # Origami
    # "PO"  # Pour Over
    # "RC"  # Reserve
    # "SBB",  # Unknown, not listed in the filters
}


class StarbucksCNSpider(JSONBlobSpider):
    download_timeout = 30
    name = "starbucks_cn"
    item_attributes = {"brand": "星巴克", "brand_wikidata": "Q37158", "extras": Categories.COFFEE_SHOP.value}
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,  # Ensure that EN processing happens before ZH items are fetched,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }
    locations_key = "data"
    en_items = {}

    def start_requests(self):
        for lat, lon in country_iseadgg_centroids(["CN"], 79):
            yield JsonRequest(
                url=f"https://www.starbucks.com.cn/api/stores/nearby?lat={lat}&lon={lon}&limit=1000&locale=EN&features=&radius=100000",
                meta={"lat": lat, "lon": lon, "locale": "EN"},
            )
            # yield JsonRequest(
            #     url=f"https://www.starbucks.com.cn/api/stores/nearby?lat={lat}&lon={lon}&limit=1000&locale=ZH&features=&radius=100000",
            #     meta={"locale": "ZH"},
            # )

    def parse(self, response: Response) -> Iterable[Feature]:
        features = self.extract_json(response)
        if response.meta["locale"] == "EN":
            en_items = {item["ref"]: item for item in self.parse_feature_array(response, features)}
            yield JsonRequest(
                url=f"https://www.starbucks.com.cn/api/stores/nearby?lat={response.meta['lat']}&lon={response.meta['lon']}&limit=1000&locale=ZH&features=&radius=100000",
                meta={"locale": "ZH", "item_dict": en_items},
            )
        else:
            zh_items = {item["ref"]: item for item in self.parse_feature_array(response, features)}
            yield from merge_items({"en": response.meta["item_dict"], "zh": zh_items}, "zh")

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["street_address"] = location["address"]["streetAddressLine1"]
        item["addr_full"] = clean_address(
            [
                location["address"].get("streetAddressLine1"),
                location["address"].get("streetAddressLine2"),
                location["address"].get("streetAddressLine3"),
                location["address"].get("city"),
                location["address"].get("postalCode"),
            ]
        )
        for feature in location["features"]:
            if match := FEATURE_MAPPING.get(feature):
                apply_yes_no(match, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_feature/{feature}")
        yield item
        # if response.meta["locale"] == "EN":
        #     self.en_items[item["ref"]] = item
        # else:
        #     en_item = self.en_items.pop(item["ref"])
        #     yield get_merged_item({"en": en_item, "zh": item}, "zh")
