from typing import Iterable

from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class PradaSpider(YextAnswersSpider):
    name = "prada"
    item_attributes = {"brand": "Prada", "brand_wikidata": "Q193136"}
    endpoint = "https://cdn.yextapis.com/v2/accounts/me/search/vertical/query"
    api_key = "61119b3d853ae12bf41e7bd9501a718b"
    experience_key = "prada-experience"
    feature_type = "prada-locations"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item["website"] = "https://www.prada.com/us/en/store-locator/" + location["slug"]
        item["branch"] = item.pop("name").removeprefix("Prada ")
        yield item
