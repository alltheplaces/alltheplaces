from typing import Iterable

from geonamescache import GeonamesCache
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.country_utils import get_locale
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider

VOLKSWAGEN_SHARED_ATTRIBUTES = {"brand": "Volkswagen", "brand_wikidata": "Q246"}
VOLKSWAGEN_COMMERCIAL_VEHICLES_SHARED_ATTRIBUTES = {
    "brand": "Volkswagen Commercial Vehicles",
    "brand_wikidata": "Q699709",
}


class VolkswagenSpider(JSONBlobSpider):
    download_timeout = 30
    name = "volkswagen"
    locations_key = "dealers"
    start_urls = ["https://www.vw.com/en.global-config.json"]
    no_refs = True

    BRAND_MAPPING = {"V": VOLKSWAGEN_SHARED_ATTRIBUTES, "N": VOLKSWAGEN_COMMERCIAL_VEHICLES_SHARED_ATTRIBUTES}

    SERVICES_MAPPING = {
        "SERVICE": Extras.CAR_REPAIR,
        "MOT": "service:vehicle:inspection",
        "USED_PC": Extras.USED_CAR_SALES,
    }

    countries = {}

    for country in GeonamesCache().get_countries().keys():
        if lang := get_locale(country):
            countries[country] = lang

    countries.pop("BE")  # volkswagen_be spider
    countries.pop("BW")  # included in ZA
    countries.pop("NA")  # included in ZA

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.fetch_json)

    def fetch_json(self, response):
        signature = response.json()["spaAsyncConfig"]["serviceConfigEndpoint"]["signature"]
        config = response.json()["spaAsyncConfig"]["featureHubModel"]["featureAppsForFeatureAppService"][
            "/content/vwa-ngw18-feature-apps/dealer-selector"
        ]
        base_url = config["baseUrl"]
        api_key = config["featureAppApiKey"]

        for content in ["onehub_pkw", "onehub_nfz"]:
            for country, language in self.countries.items():
                url = (
                    f'{base_url}/bff-search/dealers?serviceConfigEndpoint={{"endpoint":{{"type":"publish",'
                    f'"country":"{country.lower()}","language":"{language.split("-")[0]}","content":"{content}",'
                    f'"envName":"prod","testScenarioId":null}},"signature":"{signature}"}}'
                    f'&lufthansaApiKey={api_key}&query={{"type":"DEALER","language":"{language}",'
                    f'"countryCode":"{country}","dealerServiceFilter":[],"contentDealerServiceFilter":[],"usePrimaryTenant":true,"name":" "}}'
                )

                yield JsonRequest(
                    url=url,
                    callback=self.check_status,
                    meta={
                        "handle_httpstatus_list": [500],
                        "dont_retry": True,  # If we try an unknown country we get a 500 error and it's pointless retrying
                        "country": country,
                        "language": language,
                    },
                )

    def check_status(self, response):
        if response.status == 500:
            self.crawler.stats.set_value(
                f"atp/{self.name}/no_dealers_found/{response.meta['country']}", f"{response.meta['language']}"
            )
            return
        else:
            yield from self.parse(response)

    def pre_process_data(self, feature: dict):
        if feature.get("contact") and feature["contact"].get("website"):
            if not feature["contact"]["website"].startswith("http"):
                feature["contact"]["website"] = "".join(["https://", feature["contact"]["website"]])

    def post_process_item(self, item, response, location):
        item["lat"], item["lon"] = location["coordinates"]
        if item["country"] is None:
            item["country"] = response.meta["country"]

        if match := self.BRAND_MAPPING.get(location["brand"].upper()):
            item["brand"] = match["brand"]
            item["brand_wikidata"] = match["brand_wikidata"]
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{location['brand']}")

        # Some provided states are actually countries, where one country's search gives results for other nearby countries
        if item["state"] in ["Botswana", "Namibia"]:
            item["country"] = item.pop("state")

        if "rawServices" in location:
            apply_category(Categories.SHOP_CAR, item)
            for service in location["rawServices"]:
                if match := self.SERVICES_MAPPING.get(service):
                    apply_yes_no(match, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_service/{service}")

        if "businessHours" in location and len(location["businessHours"]) > 0:
            item["opening_hours"] = OpeningHours()
            for day in location["businessHours"]:
                if len(day["times"]) == 0:
                    continue
                for time in day["times"]:
                    try:
                        item["opening_hours"].add_range(DAYS[day["dayOfWeek"] - 1], time["from"], time["till"])
                    except ValueError:
                        pass

        yield item
