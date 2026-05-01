import json
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MarieCurieGBSpider(JSONBlobSpider):
    name = "marie_curie_gb"
    item_attributes = {"brand": "Marie Curie", "brand_wikidata": "Q16997351"}
    locations_key = ["data", "metaobjects", "edges"]
    drop_attributes = {"twitter", "facebook"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        token = "aa7a1095cd246c1bce6b67ca66635634"
        domain = "shop.mariecurie.org.uk"
        version = "2024-07"
        yield JsonRequest(
            url=f"https://{domain}/api/{version}/graphql.json",
            headers={"X-Shopify-Storefront-Access-Token": token},
            data={
                "query": """
                    {
                        metaobjects(type: "store_location", first: 250) {
                            edges {
                                node {
                                    id
                                    handle
                                    title: field(key: "title") {
                                        value
                                    }
                                    latitude: field(key: "latitude") {
                                        value
                                    }
                                    longitude: field(key: "longitude") {
                                        value
                                    }
                                    address: field(key: "address") {
                                        value
                                    }
                                    email: field(key: "email_address") {
                                        value
                                    }
                                    phone: field(key: "phone_number") {
                                        value
                                    }
                                    hours: field(key: "opening_hours") {
                                        value
                                    }
                                }
                            }
                        }
                    }""",
            },
        )

    def parse_feature_array(self, response: TextResponse, feature_array: list) -> Iterable[Feature]:
        for feature in feature_array:
            if feature is None:
                continue
            feature = feature["node"]
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature) or []

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature["handle"]
        for key in list(feature.keys()):
            if isinstance(feature[key], dict) and "value" in feature[key]:
                feature[key] = feature[key]["value"]
        feature["address"] = json.loads(feature["address"])["children"][0]["children"][0]["value"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Marie Curie Charity Shop ", "")
        item["country"] = "GB"
        item.pop("lat", None)
        item.pop("lon", None)
        apply_category(Categories.SHOP_CHARITY, item)
        yield item
