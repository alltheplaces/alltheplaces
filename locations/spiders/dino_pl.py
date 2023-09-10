import json
import re

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DinoPLSpider(Spider):
    name = "dino_pl"
    item_attributes = {"brand": "Dino", "brand_wikidata": "Q11694239"}
    allowed_domains = ["marketdino.pl", "api-dino.appchance.shop"]

    def start_requests(self):
        yield Request(
            url="https://marketdino.pl/external/map/_next/static/chunks/pages/index-d599ac5e0a5fa37c.js",
            callback=self.parse_decryption_params,
        )

    def parse_decryption_params(self, response):
        if m := re.search(r'\.from\("([0-9a-f]{64})","hex"\)', response.text):
            key = m.group(1)
        if m := re.search(r'\.from\("([0-9a-f]{32})","hex"\)', response.text):
            iv = m.group(1)
        yield Request(
            url="https://api-dino.appchance.shop/api/v1/dino_content/geofile/",
            meta={"key": key, "iv": iv},
            callback=self.parse_encrypted_geojson,
        )

    def parse_encrypted_geojson(self, response):
        aesgcm = AESGCM(bytes.fromhex(response.meta["key"]))
        geojson = json.loads(
            aesgcm.decrypt(bytes.fromhex(response.meta["iv"]), bytes.fromhex(response.text), None).decode("utf-8")
        )
        for location in geojson["features"]:
            if location["properties"]["status"] != "MARKET OTWARTY":  # "MARKET OPEN"
                continue
            item = DictParser.parse(location["properties"])
            item["geometry"] = location["geometry"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(
                ["Mo", "Tu", "We", "Th", "Fr", "Sa"], *location["properties"]["weekHours"].split("-", 1)
            )
            item["opening_hours"].add_range("Su", *location["properties"]["sundayHours"].split("-", 1))
            yield item
