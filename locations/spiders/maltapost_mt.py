from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

LETTERBOX = 1
POST_OFFICE = 2
SUB_POST_OFFICE = 4


class MaltapostMTSpider(Spider):
    name = "maltapost_mt"
    item_attributes = {"operator": "MaltaPost", "operator_wikidata": "Q4171158"}
    allowed_domains = ["maltapost-letterboxes.cyberpasstg.net"]
    # The "letterboxes & outlets" finder on maltapost.com is an iframe of this app; "[ALL]" returns every
    # point of the requested types. Type 5 (stamp vendors) is not requested.
    start_urls = [
        f"https://maltapost-letterboxes.cyberpasstg.net/maltapost/BusinessLogic/TagPublic?TagCity=%5BALL%5D&TagTypes={LETTERBOX},{POST_OFFICE},{SUB_POST_OFFICE}"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for tag in response.json()["Rows"]:
            if tag["M_TagIsDeleted"]:
                continue
            item = Feature()
            item["ref"] = tag["M_TagID"]
            item["lat"], item["lon"] = tag["M_TagLatitude"], tag["M_TagLongitude"]
            item["city"] = tag["M_TagCityName"]
            # e.g. "Triq It-Tamal - Ħal Tarxien" or "Troy Stationery - 1 Triq Il-Kapuċċini - Il-Kalkara"
            location = " ".join(tag["M_TagLocationName"].split())
            item["addr_full"] = location
            item["extras"]["ref:maltapost"] = tag["M_TagCode"]
            if tag["M_TagTypeID"] == LETTERBOX:
                apply_category(Categories.POST_BOX, item)
            elif tag["M_TagTypeID"] == POST_OFFICE:
                item["branch"] = tag["M_TagCityName"]
                apply_category(Categories.POST_OFFICE, item)
            elif tag["M_TagTypeID"] == SUB_POST_OFFICE:
                # Sub post offices are counters inside shops and local councils.
                parts = [p.strip() for p in location.split(" - ") if not p.strip().isdigit()]
                item["name"] = parts[0] if len(parts) > 1 else location
                item["extras"]["post_office"] = "post_partner"
                apply_category(Categories.GENERIC_POI, item)
            else:
                continue
            yield item
