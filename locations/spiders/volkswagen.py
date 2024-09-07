from typing import Iterable

import pycountry
from babel import Locale, UnknownLocaleError
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider

FEATURES_MAPPING = {
    "VEHICLESERVICES": Extras.CAR_REPAIR,
}

SERVICES_MAPPING = {
    "MOT": "service:vehicle:mot",
}


class VolkswagenBWNAZASpider(JSONBlobSpider):
    download_timeout = 30
    name = "volkswagen"
    item_attributes = {"brand": "Volkswagen", "brand_wikidata": "Q246"}
    locations_key = "dealers"
    start_urls = ["https://www.vw.com/en.global-config.json"]

    countries = {}
    for country in pycountry.countries:
        try:
            lang = str(Locale.parse("und_" + country.alpha_2))
            countries[country.alpha_2] = lang.replace("_", "-")
        except UnknownLocaleError:
            pass

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

        for country, language in self.countries.items():
            url = (
                base_url
                + '/bff-search/dealers?serviceConfigEndpoint={"endpoint":{"type":"publish","country":"'
                + country.lower()
                + '","language":"'
                + language.split("-")[0]
                + '","content":"onehub_pkw","envName":"prod","testScenarioId":null},"signature":"'
                + signature
                + '"}&lufthansaApiKey='
                + api_key
                + '&query={"type":"DEALER","language":"'
                + language
                + '","countryCode":"'
                + country
                + '","dealerServiceFilter":[],"contentDealerServiceFilter":[],"usePrimaryTenant":true,"name":" "}'
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

    def post_process_item(self, item, response, location):
        item["lat"], item["lon"] = location["coordinates"]
        if item["country"] is None:
            item["country"] = response.meta["country"]
        if location["brand"] != "V":
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{location['brand']}")

        # Some provided states are actually countries, where one country's search gives results for other nearby countries
        if item["state"] in ["Botswana", "Namibia"]:
            item["country"] = item.pop("state")

        if "features" in location:
            for feature in location["features"]:
                if match := FEATURES_MAPPING.get(feature):
                    apply_yes_no(match, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_feature/{feature}")
        if "rawServices" in location:
            apply_yes_no("service:vehicle:mot", item, "MOT" in location["rawServices"])
            for service in location["rawServices"]:
                if match := SERVICES_MAPPING.get(service):
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

        apply_category(Categories.SHOP_CAR, item)
        yield item
