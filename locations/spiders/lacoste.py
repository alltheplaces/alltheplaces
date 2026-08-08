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
        # c_liveOnPages marks stores that have no page on lacoste.com; both their
        # websiteUrl and their slug point at URLs that do not exist.
        if not location.get("c_liveOnPages"):
            item["website"] = None
            yield item
            return

        # websiteUrl is unusable even for live stores: absent on some, and elsewhere
        # pointing at /us with utm parameters and sometimes a doubled slash. Build the
        # URL from the slug instead and localise it by country.
        path = location["slug"].strip("/").removeprefix("us/stores/")
        market = LOCALISED_MARKETS.get(item["country"], "us")
        item["website"] = f"https://www.lacoste.com/{market}/stores/{path}"
        item["extras"]["@source_uri"] = item["website"]
        yield item
