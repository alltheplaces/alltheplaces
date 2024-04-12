import scrapy

from locations.items import Feature


class NespressoSpider(scrapy.Spider):
    name = "nespresso"
    allowed_domains = ["nespresso.com"]
    item_attributes = {"brand": "Nespresso", "brand_wikidata": "Q301301"}

    def start_requests(self):
        countries = [
            "AD",
            "AE",
            "AR",
            "AT",
            "AU",
            "BE",
            "BH",
            "BL",
            "BR",
            "CA",
            "CH",
            "CI",
            "CL",
            "CN",
            "CO",
            "CY",
            "CZ",
            "DE",
            "DK",
            "DZ",
            "EG",
            "ES",
            "FI",
            "FR",
            "GB",
            "GF",
            "GP",
            "GR",
            "HK",
            "HU",
            "IE",
            "IL",
            "IT",
            "JP",
            "KR",
            "KW",
            "LB",
            "LU",
            "MA",
            "MF",
            "MQ",
            "MU",
            "MX",
            "MY",
            "NL",
            "NO",
            "NZ",
            "OM",
            "PL",
            "PT",
            "QA",
            "RE",
            "RO",
            "RU",
            "SA",
            "SE",
            "SK",
            "TH",
            "TR",
            "TW",
            "US",
            "YT",
            "ZA",
        ]

        base_url = "https://www.nespresso.com/storelocator/app/find_poi-v4.php?country={country}&lang=EN"

        for country in countries:
            url = base_url.format(country=country)
            yield scrapy.Request(url, callback=self.parse, meta={"country": country})

    def parse(self, response):
        stores = response.json()

        for store in stores:
            properties = {
                "ref": store["point_of_interest"]["point_of_interest_id"]["id"],
                "name": store["point_of_interest"]["address"]["name"]["company_name_type"]["name"]["name"],
                "street_address": store["point_of_interest"]["address"]["address_line"],
                "city": store["point_of_interest"]["address"]["city"]["name"],
                "postcode": store["point_of_interest"]["address"]["postal_code"],
                "country": response.meta["country"],
                "lat": store["position"]["latitude"],
                "lon": store["position"]["longitude"],
                "phone": store["point_of_interest"]["phone"],
            }

            yield Feature(**properties)
