import json
import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BarriqueDENLSpider(JSONBlobSpider):
    name = "barrique_de_nl"
    item_attributes = {"brand": "Barrique", "brand_wikidata": "Q114133164"}
    start_urls = ["https://www.barrique.de/ladengeschaefte"]

    def extract_json(self, response: Response, **kwargs: Any) -> Any:
        return json.loads(response.css("div.maps2::attr(data-pois)").get())

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature["uid"]
        # Emails are unreliable: the mailto href is stale/mismatched on several store pages
        # (e.g. uid 38's href points to a different store than its own display text), so
        # email is intentionally not extracted here.
        if phone := re.search(
            r"(?:Tel(?:efon)?\.?:?|T:)(?:&nbsp;|\s)*([+(\d][\d\s/().-]*\d)", feature["infoWindowContent"]
        ):
            feature["phone"] = phone.group(1).replace("/", " ")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Barrique ").strip()
        item["website"] = response.url
        item["country"] = "NL" if "Nederland" in item["addr_full"] else "DE"
        apply_category(Categories.SHOP_WINE, item)
        yield item
