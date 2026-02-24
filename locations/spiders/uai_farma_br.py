from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class UaiFarmaBRSpider(JSONBlobSpider):
    name = "uai_farma_br"
    item_attributes = {"brand": "Uai Farma", "brand_wikidata": "Q123437153"}
    start_urls = [
        "https://siteassets.parastorage.com/pages/pages/thunderbolt?dfVersion=1.2710.0&fileId=c5c52d56.bundle.min&isHttps=true&isUrlMigrated=true&metaSiteId=5086618d-a676-4cea-8cd8-81ce9c36563a&module=thunderbolt-features&pageId=30abd6_1266b112fa432f54a9402b97d9db8c5c_1011.json&quickActionsMenuEnabled=false&siteId=1de60783-a0c0-48e8-90c0-815304bf35be&siteRevision=1011"
    ]
    no_refs = True
    locations_key = ["props", "render", "compProps", "comp-kjy6o783", "mapData", "locations"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["phone"] = feature.get("description", "").replace("\t", "; ")
        item["branch"] = item.pop("name")
        apply_category(Categories.PHARMACY, item)
        yield item
