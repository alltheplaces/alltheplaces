from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

MAZDA_SHARED_ATTRIBUTES = {"operator": "Mazda", "operator_wikidata": "Q35996"}

class MazdaJPSpider(JSONBlobSpider):
    name = "mazda_jp"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["ssl.mazda.co.jp"]
    locations_key = ["Shops"]

    def start_requests(self) -> Iterable[JsonRequest]:
        for coordinates in country_iseadgg_centroids(["JP"], 79):
            yield JsonRequest(url="https://ssl.mazda.co.jp/api/v1/shopslist/?latitude={}&longitude={}".format(coordinates[0], coordinates[1]))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["DealerId"]
        item["name"] = feature["DealerName"]
        item["street_address"] = merge_address_lines([feature["Address"]["Address1"], feature["Address"]["Address2"]])
        item["phone"] = feature["Contact"]["PhoneNumber"]
        item["extras"]["fax"] = feature["Contact"]["FaxNumber"]
        item["website"] = feature["Contact"]["WebsiteUrl"]
        services = [service["Service"] for service in feature["Services"]]
        if "新車" in services or "中古車" in services:
            # New car or used car sales
            sales_item = item.deepcopy()
            sales_item["ref"] = sales_item["ref"] + "_Sales"
            apply_category(Categories.SHOP_CAR, sales_item)
            yield sales_item
        if "サービス" in services:
            # Car repair
            service_item = item.deepcopy()
            service_item["ref"] = service_item["ref"] + "_Service"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item
