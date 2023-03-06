import scrapy
from locations.items import Feature


class SmartSpider(scrapy.Spider):
    name = "smart"
    item_attributes = {"brand": "Smart", "brand_wikidata": "Q156490"}
    base_url = "https://www.smart.mercedes-benz.com/api/dealer-locator"
    available_country = [
        "AR",
        "AQ",
        "AU",
        "AT",
        "BE",
        "BG",
        "BR",
        "CA",
        "CH",
        "CN",
        "CY",
        "CZ",
        "DE",
        "DK",
        "ES",
        "FI",
        "FR",
        "GB",
        "GR",
        "HK",
        "HR",
        "HU",
        "ID",
        "IN",
        "IE",
        "IT",
        "JP",
        "LB",
        "LI",
        "LK",
        "LU",
        "MO",
        "MX",
        "MT",
        "MY",
        "NL",
        "NO",
        "NZ",
        "PL",
        "PT",
        "RO",
        "RU",
        "RS",
        "SK",
        "SI",
        "SE",
        "TR",
        "TW",
        "UA",
        "US",
        "VN",
        "ZA",
    ]

    def start_requests(self):
        for country in self.available_country:
            yield scrapy.Request(f"{self.base_url}?userCountry={country}")

    def parse(self, response):
        dealer_list = response.json().get("dealersList")
        for row in dealer_list:
            lat = row.get("address").get("latitude")
            lon = row.get("address").get("longitude")
            properties = {
                "ref": row.get("baseInfo").get("externalId"),
                "name": row.get("baseInfo").get("name1"),
                "brand": self.name,
                "city": row.get("address")["city"],
                "state": row.get("address").get("region").get("region"),
                "street_address": row.get("address").get("line1"),
                "postcode": row.get("address").get("zipcode"),
                "country": row.get("address").get("country"),
                "lat": float(lat) if lat else None,
                "lon": float(lon) if lon else None,
                "phone": row.get("contact").get("phone"),
                "email": row.get("contact").get("email"),
                "website": row.get("contact").get("website"),
                "facebook": row.get("contact").get("facebook"),
            }

            yield Feature(**properties)
