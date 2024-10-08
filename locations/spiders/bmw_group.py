import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BmwGroupSpider(scrapy.Spider):
    name = "bmw_group"
    available_countries = [
        "LU",
        "JP",
        "FO",
        "DK",
        "AR",
        "CA",
        "AE",
        "DZ",
        "RO",
        "AU",
        "KY",
        "SK",
        "IQ",
        "TM",
        "VN",
        "DE",
        "SE",
        "SR",
        "HU",
        "PT",
        "AG",
        "BE",
        "BD",
        "LK",
        "MD",
        "QA",
        "RS",
        "GH",
        "ID",
        "RE",
        "SV",
        "BG",
        "UA",
        "MQ",
        "KH",
        "LY",
        "IE",
        "NZ",
        "JO",
        "BL",
        "CW",
        "CZ",
        "LA",
        "LB",
        "MY",
        "GT",
        "NL",
        "PS",
        "ZM",
        "MO",
        "CH",
        "MG",
        "SG",
        "GR",
        "TW",
        "US",
        "AW",
        "BR",
        "CL",
        "EC",
        "IN",
        "BH",
        "SI",
        "BB",
        "PL",
        "DO",
        "MX",
        "SA",
        "TN",
        "FR",
        "JM",
        "RW",
        "BJ",
        "LT",
        "TR",
        "LC",
        "PH",
        "NP",
        "PF",
        "MM",
        "AT",
        "PA",
        "BM",
        "RU",
        "AM",
        "AL",
        "BA",
        "NC",
        "KZ",
        "MA",
        "PK",
        "UY",
        "BN",
        "BS",
        "TH",
        "GP",
        "KW",
        "AZ",
        "IL",
        "ME",
        "HN",
        "KR",
        "MU",
        "NO",
        "OM",
        "NG",
        "IS",
        "TT",
        "GF",
        "ZA",
        "BO",
        "GB",
        "GE",
        "KG",
        "CO",
        "MT",
        "HR",
        "CY",
        "HT",
        "SC",
        "EE",
        "GU",
        "PE",
        "KE",
        "ES",
        "CR",
        "PY",
        "FI",
        "IT",
        "MK",
        "BY",
        "LV",
    ]
    brand_mapping = {
        "BMW": {"brand": "BMW", "brand_wikidata": "Q26678"},
        "BMW_I": {"brand": "BMW i", "brand_wikidata": "Q796784"},
        "ROLLS_ROYCE": {"brand": "Rolls-Royce", "brand_wikidata": "Q243278"},
        "BMW_M": {"brand": "BMW M", "brand_wikidata": "Q173339"},
        "MINI": {"brand": "Mini", "brand_wikidata": "Q116232"},
        "BMW_MOTORBIKE": {"brand": "BMW Motorrad", "brand_wikidata": "Q249173"},
    }

    def start_requests(self):
        for country in self.available_countries:
            url = f"https://www.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/DE/pois?brand=BMW_BMWI_BMWM&cached=off&language=en&lat=0&lng=0&maxResults=7000&showAll=true&unit=km&country={country}"
            yield scrapy.Request(
                url=url, callback=self.parse, headers={"Accept": "application/json", "Content-Type": "application/json"}
            )

    def parse(self, response):
        response = response.json().get("data").get("pois")
        for data in response:
            data["street_address"] = data.pop("street")
            occurrences = self.get_num_of_brands_per_location(response, data.get("key"))
            item = DictParser.parse(data)
            item["ref"] = data.get("key")
            item["phone"] = data.get("attributes", {}).get("phone")
            item["email"] = data.get("attributes", {}).get("mail")
            item["website"] = data.get("attributes", {}).get("homepage")
            if occurrences > 1:
                # If there are more than one brand per location, we set it to the mother brand, BMW
                item["brand"] = self.brand_mapping["BMW"]["brand"]
                item["brand_wikidata"] = self.brand_mapping["BMW"]["brand_wikidata"]
            else:
                item["brand"] = self.brand_mapping[data.get("category")]["brand"]
                item["brand_wikidata"] = self.brand_mapping[data.get("category")]["brand_wikidata"]

            if item["brand"] == "BMW Motorrad":
                apply_category(Categories.SHOP_MOTORCYCLE, item)
            else:
                apply_category(Categories.SHOP_CAR, item)

            yield item

    def get_num_of_brands_per_location(self, data, key):
        # A dealer can have multiple brands, so we need to check if there are more than one brand per location
        return sum(1 for pois in data if key == pois.get("key"))
