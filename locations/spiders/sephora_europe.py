from collections import Counter
from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_CZ, DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

COUNTRIES = {
    "FR": {
        "domain": "www.sephora.fr",
        "sfcc_site": "Sephora_FR",
        "locale": "fr_FR",
    },
    "DE": {
        "domain": "www.sephora.de",
        "sfcc_site": "Sephora_DE",
        "locale": "de_DE",
    },
    "IT": {
        "domain": "www.sephora.it",
        "sfcc_site": "Sephora_IT",
        "locale": "it_IT",
    },
    "ES": {
        "domain": "www.sephora.es",
        "sfcc_site": "Sephora_ES",
        "locale": "es_ES",
    },
    "PT": {
        "domain": "www.sephora.pt",
        "sfcc_site": "Sephora_ES",
        "locale": "pt_PT",
    },
    "PL": {
        "domain": "www.sephora.pl",
        "sfcc_site": "Sephora_PL",
        "locale": "pl_PL",
    },
    "CZ": {
        "domain": "www.sephora.cz",
        "sfcc_site": "Sephora_PL",
        "locale": "cs_CZ",
    },
    "RO": {
        "domain": "www.sephora.ro",
        "sfcc_site": "Sephora_RO",
        "locale": "ro_RO",
    },
    "GR": {
        "domain": "www.sephora.gr",
        "sfcc_site": "Sephora_RO",
        "locale": "el_GR",
    },
    "SE": {
        "domain": "www.sephora.se",
        "sfcc_site": "Sephora_Scandinavia",
        "locale": "sv_SE",
    },
    "DK": {
        "domain": "www.sephora.dk",
        "sfcc_site": "Sephora_Scandinavia",
        "locale": "da_DK",
    },
    "TR": {
        "domain": "www.sephora.com.tr",
        "sfcc_site": "Sephora_TR",
        "locale": "tr_TR",
    },
}


class SephoraEuropeSpider(JSONBlobSpider):
    name = "sephora_europe"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        for country_code, config in COUNTRIES.items():
            # The store locator's own search endpoint: a radius wide enough returns every store of the site.
            yield Request(
                f"https://{config['domain']}/on/demandware.store/Sites-{config['sfcc_site']}-Site/{config['locale']}"
                "/Stores-FindNearestStores?latitude=48&longitude=12&searchedRadius=5000",
                # Akamai Bot Manager blocks direct requests.
                meta={"zyte_api": {"httpResponseBody": True, "httpResponseHeaders": True, "geolocation": country_code}},
            )

    def extract_json(self, response: TextResponse) -> list[dict]:
        features = response.json()["locations"]
        # Some stores carry the country's customer service number instead of their own.
        phones = Counter(feature.get("phone") for feature in features)
        for feature in features:
            if phones[feature.get("phone")] > 1:
                feature["phone"] = None
        return features

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # Store IDs are only unique within a country's site.
        item["ref"] = item["website"]
        item["branch"] = item.pop("name", None)

        if hours := feature.get("scheduleForJsonLD"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                hours if isinstance(hours, str) else "; ".join(hours),
                days=DAYS_CZ if item.get("country") == "CZ" else DAYS_EN,
            )

        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
