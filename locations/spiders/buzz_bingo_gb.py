import re
from typing import AsyncIterator

from scrapy.http import JsonRequest, Response

from locations.categories import apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BuzzBingoGBSpider(StructuredDataSpider):
    name = "buzz_bingo_gb"
    item_attributes = {"brand": "Buzz Bingo", "brand_wikidata": "Q60746117"}
    wanted_types = ["LocalBusiness"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.addressy.com/LocationServices/LocationManagement/GetLists/v1.00/json4.ws"
            "?Key=WK33-FX84-AM52-PJ14&listID=ffe05512-87d2-4142-929f-cffc5bf81a4c",
            callback=self.parse_api,
        )

    def parse_api(self, response: Response):
        for location in response.json()["Locations"]:
            slug = re.sub(r"[^a-z0-9]+", "-", location["Name"].lower()).strip("-")
            yield response.follow(
                f"https://www.buzzbingo.com/club/{slug}.html",
                callback=self.parse_sd,
                meta={"ref": location["MetaInfo"]["buzzid"]},
            )

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.meta.get("ref") or response.url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html")
        item["branch"] = item.pop("name").removeprefix("Buzz Bingo ")
        item.pop("image", None)  # shared award logos, not per-location images
        item.pop("facebook", None)  # generic brand page, not per-location
        item.pop("twitter", None)  # generic brand account, not per-location
        # Extract per-location phone and email from LD+JSON contactPoint
        contact = ld_data.get("contactPoint", {})
        item["phone"] = contact.get("telephone")
        item["email"] = contact.get("email")
        apply_category({"gambling": "bingo;slot_machines"}, item)
        yield item
