from scrapy import Spider
from scrapy.http import JsonRequest

from locations.country_utils import CountryUtils
from locations.geo import point_locations
from locations.items import Feature


class AudiSpider(Spider):
    name = "audi"
    item_attributes = {
        "brand": "Audi",
        "brand_wikidata": "Q23317",
    }
    graphql_url = "https://dev-dealer-graphql.apps.emea.vwapps.io/"
    countries = [
        "ALB",
        "ARE",
        "ARG",
        "ARM",
        "AUS",
        "AUT",
        "AZE",
        "BEL",
        "BGR",
        "BHR",
        "BIH",
        "BLR",
        "BRA",
        "BRN",
        "CAN",
        "CHE",
        "CHL",
        "CHN",
        "CYP",
        "CZE",
        "DEU",
        "DNK",
        "ESP",
        "EST",
        "FIN",
        "FRA",
        "GBR",
        "GEO",
        "GRC",
        "HKG",
        "HRV",
        "HUN",
        "IDN",
        "IND",
        "IRL",
        "ISL",
        "ISR",
        "ITA",
        "JOR",
        "JPN",
        "KAZ",
        "KOR",
        "KWT",
        "LBN",
        "LTU",
        "LUX",
        "LVA",
        "MDA",
        "MEX",
        "MKD",
        "MLT",
        "MNE",
        "MYS",
        "NLD",
        "NOR",
        "NZL",
        "OMN",
        "PHL",
        "POL",
        "PRT",
        "QAT",
        "ROU",
        "RUS",
        "SAU",
        "SGP",
        "SRB",
        "SVK",
        "SVN",
        "SWE",
        "THA",
        "TUR",
        "TWN",
        "UKR",
        "USA",
        "UZB",
        "ZAF",
    ]

    def start_requests(self):
        for iso_3 in self.countries:
            iso_2 = CountryUtils().to_iso_alpha2_country_code(country_str=iso_3)
            for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", iso_2):
                yield JsonRequest(
                    url=self.graphql_url,
                    method="POST",
                    data={
                        "operationName": "Dealer",
                        "variables": {"country": iso_3, "lat": float(lat), "lng": float(lon)},
                        "query": "query Dealer($country: String, $services: String, $lng: Float!, $lat: Float!) {\n  dealersByGeoLocation(\n  limit: 100\n    country: $country\n    serviceFilter: $services\n  lat: $lat\n lng: $lng\n) {\n    dealers {\n      ...FragmentDealerFields\n      __typename\n    }\n    meta {\n      resultCount\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment FragmentDealerFields on Dealer {\n  dealerId\n  vCardUrl\n matPrimaryCode\n  kvpsPartnerKey\n  name\n  address\n  latitude \n  longitude\n houseNumber\n  street\n region\n  city\n  zipCode\n  services\n  distance\n  phone\n  additionalData {\n    displayName\n    locationName\n    __typename\n  }\n  openingHours {\n    departments {\n      id\n      departmentName\n      openingHours {\n        id\n        open\n        timeRanges {\n          openTime\n           \n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n",
                    },
                    meta={"country_code": iso_2},
                )

    def parse(self, response):
        data = response.json()
        store_data = data.get("data").get("dealersByGeoLocation").get("dealers")
        count = data.get("data").get("dealersByGeoLocation").get("meta").get("resultCount")
        assert count < 100
        for store in store_data:
            properties = {
                "ref": store.get("dealerId"),
                "name": store.get("name"),
                "addr_full": " ".join(store.get("address")),
                "housenumber": store.get("houseNumber"),
                "street": store.get("street"),
                "street_address": store.get("address")[0],
                "city": store.get("city"),
                "state": store.get("region"),
                "phone": store.get("phone"),
                "postcode": store.get("zipCode"),
                "country": response.meta.get("country_code"),
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
            }
            yield Feature(**properties)
