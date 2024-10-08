import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class MercedesBenzGroupSpider(scrapy.Spider):
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
    ]

    brand_mapping = {
        "Mercedes-Benz": {"brand": "Mercedes-Benz", "brand_wikidata": "Q36008"},
        "Maybach": {"brand": "Maybach", "brand_wikidata": "Q35989"},
        "Smart": {"brand": "Smart", "brand_wikidata": "Q156490"},
        "Fuso": {"brand": "Fuso", "brand_wikidata": "Q36033"},
        "Setra": {"brand": "Setra", "brand_wikidata": "Q938615"},
    }
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"x-apikey": "45ab9277-3014-4c9e-b059-6c0542ad9484"}}

    def start_requests(self):
        for country in self.available_countries:
            url = f"https://api.oneweb.mercedes-benz.com/dlc-dms/v2/dealers/search?configurationExternalId=OneDLC_Dlp&country={country}&strictGeo=true&expand=false&localeLanguage=false&distance=2500km&includeApplicants=true&spellCheck=false&size=-1&searchProfileName=DLp_{country.lower()}"
            yield scrapy.Request(url=url, callback=self.get_store_info)

    def get_store_info(self, response):
        for store in response.json().get("results", []):
            url = f"https://api.oneweb.mercedes-benz.com/dlc-dms/v2/dealers/search/byId?localeLanguage=false&id={store.get('baseInfo').get('externalId')}&fields=*"
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for data in response.json().get("results", []):
            oh = OpeningHours()
            for function in data.get("functions"):
                if function.get("activityCode") != "SALES":
                    continue
                for day, hours in function.get("openingHours").items():
                    day = sanitise_day(day)
                    if not hours.get("open"):
                        continue
                    for periods in hours.get("timePeriods"):
                        oh.add_range(
                            day=day, open_time=periods.get("from"), close_time=periods.get("to"), time_format="%H:%M"
                        )

            item = DictParser.parse(data)
            address_details = data.get("address")
            base_info = data.get("baseInfo")
            item["ref"] = base_info.get("externalId")
            item["name"] = base_info.get("name1") or data.get("baseInfo").get("name2")
            item["lat"] = address_details.get("latitude")
            item["lon"] = address_details.get("longitude")
            item["opening_hours"] = oh
            if len(data.get("brands")) > 1:
                item["brand"] = self.brand_mapping.get("Mercedes-Benz").get("brand")
                item["brand_wikidata"] = self.brand_mapping.get("Mercedes-Benz").get("brand_wikidata")
            else:
                item["brand"] = data.get("brands")[0].get("brand").get("name")
                item["brand_wikidata"] = self.brand_mapping.get(item["brand"]).get("brand_wikidata")

            if isinstance(item["state"], dict):
                item["state"] = item["state"].get("region")

            apply_category(Categories.SHOP_CAR, item)

            yield item
