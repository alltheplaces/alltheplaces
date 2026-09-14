from typing import Any, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

# ISO 3166-2 subdivision codes for the provinces/regions observed in this
# spider's data, keyed by the raw "countryName" values returned by the API.
# Countries or provinces without an unambiguous subdivision code (e.g.
# Mozambique's "Maputo", which is ambiguous between Maputo City and Maputo
# Province, or Seychelles/Mauritius regions that aren't ISO subdivisions) are
# intentionally omitted so item["state"] is left unset rather than storing a
# raw display name.
STATE_CODES = {
    "South Africa": {
        "Eastern Cape": "EC",
        "Free State": "FS",
        "Gauteng": "GP",
        "KwaZulu-Natal": "KZN",
        "Limpopo Province": "LP",
        "Mpumalanga": "MP",
        "North West Province": "NW",
        "Northern Cape": "NC",
        "Western Cape": "WC",
    },
    "United Arab Emirates": {
        "Dubai": "DU",
    },
    "Zimbabwe": {
        "Harare": "HA",
        "Matabeleland South": "MS",
    },
    "Namibia": {
        "Erongo": "ER",
        "Khomas": "KH",
    },
    "Botswana": {
        "South East": "SE",
    },
    "Zambia": {
        "Lusaka": "09",
    },
    "Uganda": {
        "Central": "C",
    },
    "Kenya": {
        "Nairobi": "30",
    },
}


class PamGoldingSpider(JSONBlobSpider):
    name = "pam_golding"
    item_attributes = {"brand": "Pam Golding Properties", "brand_wikidata": "Q65051429"}
    skip_auto_cc_domain = True

    async def start(self) -> Any:
        yield JsonRequest("https://webapi.pamgolding.co.za/api/agentsoffices/search-offices", data={})

    def extract_json(self, response: Response) -> list[dict]:
        return [
            office for country in response.json() for section in country["sections"] for office in section["offices"]
        ]

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = str(location["id"])
        item["branch"] = item.pop("name")
        item["website"] = "https://www.pamgolding.co.za" + location["url"]
        item["addr_full"] = location.get("address")
        item["lat"] = location["geoPoint"]["lat"]
        item["lon"] = location["geoPoint"]["lon"]

        country_name = location["location"]["countryName"]
        province_name = location["location"]["provinceName"]
        # item["country"] is left as the raw display name here: the
        # CountryCodeCleanUpPipeline (which runs on every item) resolves it
        # to an ISO alpha-2 code via the same country name matching logic
        # exposed by locations.country_utils.CountryUtils, so all countries
        # observed in this dataset already come out correctly as e.g. "ZA".
        item["country"] = country_name
        if state := STATE_CODES.get(country_name, {}).get(province_name):
            item["state"] = state

        item["phone"] = location.get("number")
        item["email"] = location.get("email")
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
