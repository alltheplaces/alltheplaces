import scrapy

from locations.items import Feature


class SkodaSpider(scrapy.Spider):
    name = "skoda"
    item_attributes = {"brand": "Škoda", "brand_wikidata": "Q29637"}

    available_countries = {
        260: "CZ",
        261: "PT",
        264: "IT",
        654: "SK",
        663: "IN",
        282: "ES",
        411: "LV",
        285: "TW",
        294: "CY",
        423: "TR",
        296: "BY",
        425: "HR",
        298: "SI",
        428: "SA",
        686: "LV",
        941: "IE",
        824: "NZ",
        308: "MA",
        438: "NL",
        439: "AT",
        441: "LU",
        314: "BA",
        442: "DK",
        443: "FI",
        318: "DZ",
        447: "GR",
        572: "ES",
        703: "NP",
        959: "AU",
        451: "BG",
        456: "PL",
        457: "RS",
        202: "BE",
        334: "TN",
        207: "GR",
        462: "EE",
        463: "LT",
        210: "GB",
        599: "RO",
        216: "LU",
        218: "NO",
        222: "SE",
        223: "CH",
        995: "FR",
        233: "HU",
        107: "DE",
        622: "MD",
        886: "UA",
        250: "TN",
    }

    def start_requests(self):
        for country_id, country_code in self.available_countries.items():
            yield scrapy.Request(
                f"https://retailers.skoda-auto.com/api/{country_id}/en-us/Dealers/GetDealers",
                callback=self.parse_stores,
                meta={"country_code": country_code},
            )

    def parse_stores(self, response):
        for store in response.json().get("Items"):
            address_details = store.get("Address")
            yield Feature(
                {
                    "ref": store.get("GlobalId"),
                    "name": store.get("Name"),
                    "street_address": address_details.get("street"),
                    "country": response.meta.get("country_code"),
                    "state": address_details.get("District"),
                    "city": address_details.get("City"),
                    "postcode": address_details.get("ZIP"),
                    "lat": address_details.get("Latitude"),
                    "lon": address_details.get("Longitude"),
                }
            )
