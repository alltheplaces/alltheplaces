import json
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MarieCurieGBSpider(JSONBlobSpider):
    name = "marie_curie_gb"
    item_attributes = {"brand": "Marie Curie", "brand_wikidata": "Q16997351"}
    graphql_url = "https://shop.mariecurie.org.uk/api/2024-07/graphql.json"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = ["data", "metaobjects", "edges"]
    drop_attributes = {"twitter", "facebook"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        token = "aa7a1095cd246c1bce6b67ca66635634"
        domain = "shop.mariecurie.org.uk"
        version = "2024-07"
        yield JsonRequest(
            url=f"https://{domain}/api/{version}/graphql.json",
            headers={
                # 'Content-Type': 'application/json',
                "X-Shopify-Storefront-Access-Token": token,
            },
            data={
                "query": """
\n {\n metaobjects(type:\"store_location\", first: 250) {\n edges{\n node {\n id\n handle\n title:field(key:\"title\") {\n value\n }\n latitude:field(key:\"latitude\") {\n value\n }\n longitude:field(key:\"longitude\") {\n value\n }\n address:field(key:\"address\") {\n value\n }\n email:field(key:\"email_address\") {\n value\n }\n phone:field(key:\"phone_number\") {\n value\n }\n hours:field(key:\"opening_hours\") {\n value\n }\n }\n }\n }\n }\n
                """,
                # "variables": {"first": 250},
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
        item.pop("lat",None)
        item.pop("lon",None)
        yield item
