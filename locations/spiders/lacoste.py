import re
from typing import Iterable

from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider

# Markets lacoste.com serves a localised site for, mapped from the store's country.
# Anything else keeps the default /us site.
LOCALISED_MARKETS = {
    "AT": "at",
    "BE": "be",
    "BR": "br",
    "CH": "ch",
    "DE": "de",
    "DK": "dk",
    "ES": "es",
    "FR": "fr",
    "IT": "it",
    "KR": "kr",
    "MC": "fr",
    "MX": "mx",
    "NL": "nl",
    "PT": "pt",
    "SE": "se",
}


class LacosteSpider(YextAnswersSpider):
    name = "lacoste"
    item_attributes = {"brand": "Lacoste", "brand_wikidata": "Q309031"}
    api_key = "838385fd3ca042db80e71cce34e3d417"
    api_version = "20220511"
    environment = "PRODUCTION"
    experience_key = "locator-search-eu"
    locale = "en-US"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        # websiteUrl is missing on some stores and malformed on others ("//us/", utm
        # parameters), so build the URL from the slug and localise it by country.
        # Most slugs are "us/stores/<path>", a few are "stores/en_us/<path>".
        path = re.sub(r"^(us/)?stores/(en_us/)?", "", location["slug"].strip("/"))
        market = LOCALISED_MARKETS.get(item["country"], "us")
        item["website"] = f"https://www.lacoste.com/{market}/stores/{path}"
        item["extras"]["@source_uri"] = item["website"]
        yield item
