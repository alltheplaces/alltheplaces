from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.closeby import ClosebySpider


class UnichemNZSpider(ClosebySpider):
    name = "unichem_nz"
    item_attributes = {"brand": "Unichem", "brand_wikidata": "Q7884722"}
    api_key = "60e75b93df98a16d97499b8b8512e14f"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"] = feature["latitude"]
        item["lon"] = feature["longitude"]
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.removeprefix("Unichem ")
        if item["email"]:
            if ", " in item["email"]:
                item["email"] = item["email"].split(", ")[0]
        if item["website"]:
            item["website"] = "https://" + item["website"].replace("https://", "").replace(
                "%C2%A0-%C2%A0%C2%A0%C2%A0%C2%A0%C2%A0%C2%A0", ""
            )
        yield item
