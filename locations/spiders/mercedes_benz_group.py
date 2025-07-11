from typing import Iterable

from scrapy import Request
from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MercedesBenzGroupSpider(JSONBlobSpider):
    name = "mercedes_benz_group"
    available_countries = [
        "VN",
        "NO",
        "BR",
        "BG",
        "US",
        "SK",
        "CA",
        "CL",
        "LU",
        "FI",
        "LK",
        "PL",
        "BY",
        "AE",
        "PT",
        "DK",
        "TN",
        "LT",
        "HR",
        "VE",
        "AL",
        "MX",
        "UA",
        "RO",
        "TH",
        "JP",
        "TW",
        "AU",
        "MT",
        "EG",
        "CY",
        "EC",
        "MY",
        "PE",
        "BE",
        "RS",
        "GB",
        "IT",
        "MA",
        "ID",
        "FR",
        "RU",
        "IE",
        "DE",
        "IN",
        "LV",
        "HK",
        "CN",
        "SG",
        "SI",
        "CO",
        "CH",
        "NL",
        "EE",
        "HU",
        "BO",
        "PY",
        "AT",
        "SE",
        "TR",
        "AF",
        "NZ",
        "PH",
        "AR",
        "BN",
        "BA",
        "IS",
        "GR",
        "CZ",
        "UY",
        "ES",
        "ZA",
        "KR",
        "SA",
    ]

    BRAND_MAPPING = {
        "Mercedes-Benz": {"brand": "Mercedes-Benz", "brand_wikidata": "Q36008"},
        "Maybach": {"brand": "Maybach", "brand_wikidata": "Q35989"},
        "Smart": {"brand": "Smart", "brand_wikidata": "Q156490"},
        "Fuso": {"brand": "Fuso", "brand_wikidata": "Q36033"},
        "Setra": {"brand": "Setra", "brand_wikidata": "Q938615"},
    }
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"x-apikey": "ce7d9916-6a3d-407a-b086-fea4cbae05f6"}}
    locations_key = "dealers"

    def make_request(self, country: str, page: int = 1) -> Request:
        url = "https://api.oneweb.mercedes-benz.com/dms-plus/v3/api/dealers/market?marketCode={}&page={}&size=25&includeFields=*&localeLanguage=true".format(
            country, page
        )
        return Request(url, meta={"country": country})

    def start_requests(self) -> Iterable[Request]:
        for country in self.available_countries:
            yield self.make_request(country)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["outletId"]
        item["state"] = feature.get("address", {}).get("region", {}).get("state")
        yield item

        data = response.json()
        current_page = data["page"]["number"]
        if current_page < data["page"]["totalPages"]:
            yield self.make_request(response.meta["country"], current_page + 1)
