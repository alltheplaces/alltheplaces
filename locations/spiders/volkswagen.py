import re
from copy import deepcopy
from typing import Any, AsyncIterator, Iterable

import reverse_geocoder
from geonamescache import GeonamesCache
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.country_utils import get_locale
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

VOLKSWAGEN_SHARED_ATTRIBUTES = {"brand": "Volkswagen", "brand_wikidata": "Q246"}
VOLKSWAGEN_COMMERCIAL_VEHICLES_SHARED_ATTRIBUTES = {
    "brand": "Volkswagen Commercial Vehicles",
    "brand_wikidata": "Q699709",
}


# The API groups multiple countries under the same countryCode (e.g., FRX, LAC, LAM),
# which causes the spider to produce duplicate results when querying the API by individual country.
class VolkswagenSpider(JSONBlobSpider):
    name = "volkswagen"
    locations_key = "dealers"
    start_urls = ["https://www.vw.com/en.global-config.json"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}
    BRAND_MAPPING = {
        "V": VOLKSWAGEN_SHARED_ATTRIBUTES,
        "N": VOLKSWAGEN_COMMERCIAL_VEHICLES_SHARED_ATTRIBUTES,
        "L": VOLKSWAGEN_COMMERCIAL_VEHICLES_SHARED_ATTRIBUTES,
    }
    EXTRAS_MAPPING = {
        "MOT": "service:vehicle:inspection",
        "USED_PC": Extras.USED_CAR_SALES,
        "USED_CV": Extras.USED_CAR_SALES,
        "FCWASH": Extras.CAR_WASH,
        "PARTS": Extras.CAR_PARTS,
    }
    SERVICE_ATTRIBUTES = [
        "SERVICE",
        "COLLISION_REPAIR",
        "COLLISION_CENTER",
        "EXPRESS_SERVICE",
        "ECONOMY_SERVICE",
        "WORKSHOP",
        "VEHICLESERVICES",
        "COLLISION",
        "ACCES_CNFG",
        "DCC_ONLY",
        "PAINT_SHOP",
        "SRVONLY",
    ]
    countries = {}
    # Some countries use a different language parameter than the one returned by get_locale.
    OVERRIDE_LOCALE = {"TN": "fr-TN", "NO": "no-NO"}
    for country in GeonamesCache().get_countries().keys():
        if lang := get_locale(country):
            lang = OVERRIDE_LOCALE.get(country, lang)
            countries[country] = lang

    countries.pop("BE")  # volkswagen_be spider
    countries.pop("BW")  # included in ZA
    countries.pop("NA")  # included in ZA

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.fetch_json)

    def fetch_json(self, response: Response):
        # onehub_pkw - VOLKSWAGEN
        # onehub_nfz - COMMERCIAL VEHICLES
        for content in ["onehub_pkw", "onehub_nfz"]:
            for country, language in self.countries.items():
                url = self.build_url(response, country, language, content)
                yield JsonRequest(
                    url=url,
                    callback=self.check_status,
                    meta={
                        "handle_httpstatus_list": [500],
                        "dont_retry": True,  # If we try an unknown country we get a 500 error and it's pointless retrying
                        "country": country,
                        "content": content,
                    },
                )

    def check_status(self, response: Response):
        lang = re.search(r"%22language%22:%22([^%]+)%22", response.url).group(1)
        # some countries work only with "en" language (ID for example)
        if response.status == 500 and lang != "en":
            updated_url = re.sub(r"(%22language%22:%22)[^%]+(%22)", r"\1en\2", response.url)
            yield JsonRequest(url=updated_url, callback=self.check_status, meta=response.meta)
        elif response.status == 500:
            # porsche API is used for some countries
            content_mapping = {"onehub_pkw": "V", "onehub_nfz": "L"}
            content = content_mapping[response.meta["content"]]
            brand = self.BRAND_MAPPING.get(content)
            yield JsonRequest(
                url=f"https://groupcms-services-api.porsche-holding.com/v3/dealers/{response.meta['country']}/{content}",
                callback=VolkswagenSpider.parse_porsche_api,
                meta={"brand": brand, "country": response.meta["country"], "crawler": self.crawler},
            )
        else:
            yield from self.parse(response)

    def pre_process_data(self, feature: dict) -> None:
        if feature.get("contact") and feature["contact"].get("website"):
            if not feature["contact"]["website"].startswith("http"):
                feature["contact"]["website"] = "".join(["https://", feature["contact"]["website"]])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street")
        item["lat"], item["lon"] = feature["coordinates"]
        if item["country"] is None:
            item["country"] = response.meta["country"]
        item["ref"] = f"{item['ref']}-{feature['brand']}-{item['country']}"
        if match := self.BRAND_MAPPING.get(feature["brand"].upper()):
            item["brand"] = match["brand"]
            item["brand_wikidata"] = match["brand_wikidata"]
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{feature['brand']}")
        # Some provided states are actually countries, where one country's search gives results for other nearby countries
        if item["state"] in ["Botswana", "Namibia"]:
            item["country"] = item.pop("state")
        # Found one POI in France that geocoder marks as in ES
        if feature["address"]["countryCode"] == "FRX":
            if result := reverse_geocoder.get((item["lat"], item["lon"]), mode=1, verbose=False):
                if result["cc"] == "ES":
                    item["country"] = "FR"
        if "businessHours" in feature and len(feature["businessHours"]) > 0:
            self.parse_hours(feature["businessHours"], item)
        services = feature.get("rawServices", []) + feature.get("features", [])
        if services:
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-SHOP"
            apply_category(Categories.SHOP_CAR, shop_item)
            for service in services:
                if match := self.EXTRAS_MAPPING.get(service):
                    apply_yes_no(match, shop_item, True)
            yield shop_item
        if any(service in self.SERVICE_ATTRIBUTES for service in services):
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

    # can be used in seat and skoda spiders
    @staticmethod
    def parse_porsche_api(response: Response, **kwargs: Any) -> Iterable[Feature]:
        dealers = response.json().get("data")
        brand = response.meta.get("brand", {})
        crawler = response.meta.get("crawler")
        if len(dealers) == 0:
            crawler.stats.inc_value(f"atp/no_dealers_found/{brand.get('brand')}/{response.meta.get('country')}")
        for dealer in dealers:
            item = DictParser.parse(dealer)
            item["street_address"] = item.pop("street")
            item["ref"] = f"{dealer['bnr']}-{brand.get('brand')}"
            item["state"] = dealer.get("federalState")
            offers = dealer.get("contracts", {})
            # Locations in ME have country property equal to RS
            if item.get("lat") and item.get("lon"):
                if result := reverse_geocoder.get((item["lat"], item["lon"]), mode=1, verbose=False):
                    if item["country"] != result["cc"] and item["country"] == "RS":
                        item["country"] = result["cc"]
            item["brand"] = brand.get("brand")
            item["brand_wikidata"] = brand.get("brand_wikidata")
            if offers.get("sales"):
                shop_item = deepcopy(item)
                shop_item["ref"] = f"{item['ref']}-SHOP"
                apply_category(Categories.SHOP_CAR, shop_item)
                yield shop_item
            if offers.get("service"):
                service_item = deepcopy(item)
                service_item["ref"] = f"{item['ref']}-SERVICE"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item

    def parse_hours(self, hours: list[dict], item: Feature) -> None:
        item["opening_hours"] = OpeningHours()
        for day in hours:
            if len(day["times"]) == 0:
                continue
            for time in day["times"]:
                try:
                    item["opening_hours"].add_range(DAYS[day["dayOfWeek"] - 1], time["from"], time["till"])
                except ValueError:
                    pass

    def build_url(self, response: Response, country: str, language: str, content: str) -> str:
        signature = response.json()["spaAsyncConfig"]["serviceConfigEndpoint"]["signature"]
        config = response.json()["spaAsyncConfig"]["featureHubModel"]["featureAppsForFeatureAppService"][
            "/content/vwa-ngw18-feature-apps/dealer-selector"
        ]
        base_url = config["baseUrl"]
        api_key = config["featureAppApiKey"]
        return (
            f'{base_url}/bff-search/dealers?serviceConfigEndpoint={{"endpoint":{{"type":"publish",'
            f'"country":"{country.lower()}","language":"{language.split("-")[0]}","content":"{content}",'
            f'"envName":"prod","testScenarioId":null}},"signature":"{signature}"}}'
            f'&lufthansaApiKey={api_key}&query={{"type":"DEALER","language":"{language}",'
            f'"countryCode":"{country}","dealerServiceFilter":[],"contentDealerServiceFilter":[],"usePrimaryTenant":true,"name":" "}}'
        )
