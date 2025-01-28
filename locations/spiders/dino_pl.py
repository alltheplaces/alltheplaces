import json
import re
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DinoPLSpider(Spider):
    name = "dino_pl"
    item_attributes = {"brand": "Dino", "brand_wikidata": "Q11694239"}
    allowed_domains = ["marketdino.pl"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://marketdino.pl/external/map/index.html"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Search for the desired JavaScript file
        yield response.follow(
            url=response.xpath('//script[contains(@src,"_next/static/chunks/pages/index-")]/@src').get(""),
            callback=self.parse_decryption_params,
        )

    def parse_decryption_params(self, response):
        if m := re.search(r"""\.from\([\n ]*['"]([0-9a-f]{64})['"],[\n ]*['"]hex['"][\n ]*\)""", response.text):
            key = m.group(1)
        if m := re.search(r"""\.from\([\n ]*['"]([0-9a-f]{32})['"],[\n ]*['"]hex['"][\n ]*\)""", response.text):
            iv = m.group(1)
        if m := re.search(r"[a-z]\s*=\s*\"([0-9a-f]{40})\",", response.text):
            access_token = m.group(1)
        yield Request(
            url="https://api.marketdino.pl/api/v1/dino_content/geofile/",
            headers={"Authorization": f"token {access_token}"},
            meta={"key": key, "iv": iv},
            callback=self.parse_encrypted_geojson,
        )

    def parse_encrypted_geojson(self, response):
        aesgcm = AESGCM(bytes.fromhex(response.meta["key"]))
        geojson = json.loads(
            aesgcm.decrypt(bytes.fromhex(response.meta["iv"]), bytes.fromhex(response.text), None).decode("utf-8")
        )
        for location in geojson["features"]:
            item = DictParser.parse(location["properties"])
            item["geometry"] = location["geometry"]
            item["opening_hours"] = OpeningHours()
            if week_hours := location["properties"]["weekHours"]:
                item["opening_hours"].add_days_range(["Mo", "Tu", "We", "Th", "Fr", "Sa"], *week_hours.split("-", 1))
            if sun_hours := location["properties"]["sundayHours"]:
                item["opening_hours"].add_range("Su", *sun_hours.split("-", 1))
            yield item
