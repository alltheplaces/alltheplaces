from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BricomarchePLSpider(JSONBlobSpider):
    name = "bricomarche_pl"
    item_attributes = {"brand": "Bricomarché", "brand_wikidata": "Q2925147"}
    start_urls = ["https://www.bricomarche.pl/api/v1/pos/pos/poses.json"]
    locations_key = "results"
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Bricomarché ")
        if slug := feature.get("Slug"):
            item["website"] = urljoin("https://www.bricomarche.pl/sklep/", slug)
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
