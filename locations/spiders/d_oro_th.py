import html
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DOroTHSpider(JSONBlobSpider):
    name = "d_oro_th"
    item_attributes = {"brand": "D'Oro", "brand_wikidata": "Q119134832"}
    start_urls = [
        "https://www.powr.io/wix/map/public.json?compId=comp-jbetr2s2&instance=3Etnzb9lMkBIcrvTmr-X1MN3ITBQ0Z2X7blGe0U530Y.eyJpbnN0YW5jZUlkIjoiODM2YTEyMzEtMzRmOC00YzBjLTk1NjAtODgwODRjMjQ4ZjYwIiwiYXBwRGVmSWQiOiIxMzQwYzVlZC1hYWM1LTIzZWYtNjkzYy1lZDIyMTY1Y2ZkODQiLCJzaWduRGF0ZSI6IjIwMjMtMDYtMDFUMDg6MjE6NTAuODQ0WiIsInZlbmRvclByb2R1Y3RJZCI6ImJ1c2luZXNzIiwiZGVtb01vZGUiOmZhbHNlLCJhaWQiOiI0NTkzMDY2YS01ZWI0LTQ3NjYtYmE5Mi02ZjRmNzIzMWE1NGUiLCJzaXRlT3duZXJJZCI6IjlmYTg0ZDEwLTZmM2UtNGU2Zi1iYmIxLTcxOWQyMDIxODE2YSJ9",
    ]
    locations_key = ["content", "locations"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = html.unescape(feature.get("name", "").replace("</p>", "").replace("<p>", ""))
        item["ref"] = feature.get("idx")
        apply_category(Categories.CAFE, item)
        yield item
