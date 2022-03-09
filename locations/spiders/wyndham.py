# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem
from urllib.parse import urlparse, parse_qs

BRAND_MAP = {
    "hj": "hojo",
    "HJ": "hojo",
    "hojo": "HJ",
    "lq": "laquinta",
    "LQ": "laquinta",
    "laquinta": "LQ",
    "di": "days-inn",
    "DI": "days-inn",
    "days-inn": "DI",
    "bh": "hawthorn-extended-stay",
    "BH": "hawthorn-extended-stay",
    "hawthorn-extended-stay": "BH",
    "hr": "wyndham",
    "HR": "wyndham",
    "wyndham": "HR",
    "wg": "wingate",
    "WG": "wingate",
    "wingate": "WG",
    "se": "super-8",
    "SE": "super-8",
    "super-8": "SE",
    "bu": "baymont",
    "BU": "baymont",
    "baymont": "BU",
    "dx": "dolce",
    "DX": "dolce",
    "dolce": "DX",
    "dz": "dazzler",
    "DZ": "dazzler",
    "dazzler": "DZ",
    "wr": "wyndham-rewards",
    "WR": "wyndham-rewards",
    "wyndham-rewards": "WR",
    "kg": "knights-inn",
    "KG": "knights-inn",
    "knights-inn": "KG",
    "wt": "tryp",
    "WT": "tryp",
    "tryp": "WT",
    "aa": "americinn",
    "AA": "americinn",
    "americinn": "AA",
    "all": "wyndham-hotel-group",
    "ALL": "wyndham-hotel-group",
    "wyndham-hotel-group": "ALL",
    "ce": "caesars-entertainment",
    "CE": "caesars-entertainment",
    "caesars-entertainment": "CE",
    "mt": "microtel",
    "MT": "microtel",
    "microtel": "MT",
    "gn": "wyndham-garden",
    "GN": "wyndham-garden",
    "wyndham-garden": "GN",
    "gr": "wyndham-grand",
    "GR": "wyndham-grand",
    "wyndham-grand": "GR",
    "es": "esplendor",
    "ES": "esplendor",
    "esplendor": "ES",
    "ra": "ramada",
    "RA": "ramada",
    "ramada": "RA",
    "re": "registry-collection",
    "RE": "registry-collection",
    "registry-collection": "RE",
    "tl": "travelodge",
    "TL": "travelodge",
    "travelodge": "TL",
    "vo": "wyndham-vacations",
    "VO": "wyndham-vacations",
    "wyndham-vacations": "VO",
    "tq": "trademark",
    "TQ": "trademark",
    "trademark": "TQ",
}
BRAND_TIER_MAP = {"hr": "wy", "gr": "wy", "gn": "wy", "dz": "fe", "es": "fe"}
COUNTRIES = {
    "Canada": "CA",
    "Turkey": "TR",
    "United States": "US",
    "Mexico": "MX",
    "Honduras": "HN",
    "Chile": "CL",
    "Colombia": "CO",
}


def create_url(brand, city, state, unique_url, tier_id):
    # In the html, there is a script which this recreates
    brand_name = BRAND_MAP.get(brand)
    if not brand_name:
        brand_name = BRAND_MAP.get(tier_id.lower())
    url = brand_name + "/"
    url += city.replace(" ", "-").replace(".", "").lower()
    state_name = (
        f"-{state.replace(' ','-').lower()}"
        if state.lower() != "other than us/canada"
        else ""
    )
    url += state_name + "/"
    url += unique_url.lower() + "/"
    url += "overview"
    return url


class WyndhamSpider(scrapy.Spider):
    name = "wyndham"
    download_speed = 0.7
    allowed_domains = ["www.wyndhamhotels.com"]
    start_urls = (
        "https://www.wyndhamhotels.com/BWSServices/services/search/properties?recordsPerPage=50&pageNumber=1&brandId=ALL&countryCode=US%2CCA%2CMX",
    )

    def parse(self, response):
        data = json.loads(response.text)

        page_count = data.get("pageCount")
        parsed_url = urlparse(response.request.url)
        parsed_args = parse_qs(parsed_url.query)
        page_number = int(parsed_args["pageNumber"][0])
        if page_number <= page_count:
            next_page_number = page_number + 1
            yield scrapy.Request(
                f"https://www.wyndhamhotels.com/BWSServices/services/search/properties?recordsPerPage=50&pageNumber={next_page_number}&brandId=ALL&countryCode=US%2CCA%2CMX",
            )

        for country in data["countries"]:
            country_code = country["countryCode"]
            for state in country["states"]:
                state_name = state["stateName"]
                for city in state["cities"]:
                    city_name = city["cityName"]
                    for property_ in city["propertyList"]:
                        property_id = property_["propertyId"]
                        brand_id = property_["brandId"]
                        brand_name = property_["brand"]
                        brand_tier = property_["tierId"]
                        unique_url = property_["uniqueUrl"]
                        url = create_url(
                            brand_id, city_name, state_name, unique_url, brand_tier
                        )
                        yield scrapy.Request(
                            f"https://{self.allowed_domains[0]}/{url}",
                            self.parse_property,
                            meta={
                                "id": property_id,
                                "country_code": country_code,
                                "brand_name": brand_name,
                            },
                        )

    def parse_property(self, response):
        raw_json = re.search(
            r'<script type="application\/ld\+json"\>(.+?)\<',
            response.text,
            flags=re.DOTALL,
        )
        if not raw_json:
            return None
        data = json.loads(raw_json.group(1).replace("\t", " "))
        properties = {
            "ref": response.meta["id"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"].get("addressRegion"),
            "postcode": data["address"].get("postalCode"),
            "country": response.meta["country_code"],
            "phone": data["telephone"],
            "website": response.url,
            "brand": response.meta["brand_name"],
        }
        yield GeojsonPointItem(**properties)
