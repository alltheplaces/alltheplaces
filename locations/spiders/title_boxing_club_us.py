from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TitleBoxingClubUSSpider(scrapy.Spider):
    name = "title_boxing_club_us"
    item_attributes = {"brand": "TITLE Boxing Club", "brand_wikidata": "Q126391325"}
    start_urls = ["https://api.hubapi.com/cms/v3/hubdb/tables/121868642/rows?portalId=48754936"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json()["results"]:
            poi["values"]["street_address"] = poi["values"].pop("address")
            item = DictParser.parse(poi["values"])
            item["website"] = "https://www.titleboxingclub.com/location/" + poi["values"]["site_slug"]
            item["branch"] = item.pop("name")
            item["name"] = "TITLE Boxing Club"
            apply_category(Categories.GYM, item)
            yield item
