import re
from typing import Iterable

from locations.items import Feature
from locations.spiders.sainsburys import SainsburysSpider
from locations.spiders.tesco_gb import set_located_in
from locations.storefinders.yext_answers import YextAnswersSpider


class ArgosSpider(YextAnswersSpider):
    name = "argos"
    item_attributes = {"brand": "Argos", "brand_wikidata": "Q4789707"}
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    experience_key = "argos-locator"
    api_key = "5295de161feec2b9e1ca6f483e9f77dd"
    locale = "en-GB"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        if "Collection Point" in item["name"]:
            return
        if m := re.search(r"((?:in|inside|) Sainsbury'?s?)", item["name"], flags=re.IGNORECASE):
            item["name"] = item["name"].replace(m.group(1), "").replace("()", "").strip()
            set_located_in(SainsburysSpider.SAINSBURYS, item)
        if item["name"].endswith(" Local"):
            item["name"] = item["name"].removesuffix(" Local")
            set_located_in(SainsburysSpider.SAINSBURYS_LOCAL, item)
        item["branch"] = item.pop("name").removesuffix(" Argos")
        yield item
