import html
from typing import Iterable

from scrapy.http import Response

from locations.country_utils import CountryUtils
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import FIREFOX_LATEST

# Only markets lacoste.com actually serves a localised site for; anything
# else falls back to /us. Add a code here if a store URL 404s.
LOCALISED_MARKETS = {
    "AT",
    "BE",
    "CH",
    "CN",
    "CZ",
    "DE",
    "DK",
    "ES",
    "FI",
    "FR",
    "GR",
    "HU",
    "IT",
    "JP",
    "KR",
    "NL",
    "NO",
    "PL",
    "PT",
    "RO",
    "SE",
    "TR",
    "TW",
}


class LacosteSpider(JSONBlobSpider):
    name = "lacoste"
    item_attributes = {"brand": "Lacoste", "brand_wikidata": "Q309031"}
    start_urls = ["https://www.lacoste.com/us/stores?country=&city=&json=true"]
    custom_settings = {"USER_AGENT": FIREFOX_LATEST}
    requires_proxy = True

    def extract_json(self, response: Response) -> list:
        return response.json()["stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["name"] = html.unescape(item["name"]).strip()
        country = feature["url"].split("/")[1]
        if "taiwan" in country:
            item["country"] = "TW"
        elif country.startswith("china"):
            item["country"] = "CN"
        else:
            item["country"] = CountryUtils().to_iso_alpha2_country_code(country.replace("-", " ")) or country.title()
        market = item["country"] if item["country"] in LOCALISED_MARKETS else "us"
        item["website"] = f'https://www.lacoste.com/{market.lower()}/stores{feature["url"]}'
        item["extras"]["@source_uri"] = item["website"]
        yield item
