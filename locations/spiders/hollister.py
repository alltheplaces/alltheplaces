import scrapy

from locations.items import GeojsonPointItem
from locations.user_agents import BROSWER_DEFAULT


class HollisterSpider(scrapy.Spider):
    name = "hollister"
    item_attributes = {"brand": "Hollister"}
    allowed_domains = ["hollisterco.com"]

    # Website is blocking scrapers so I had to change the User Agent to get around this
    user_agent = BROSWER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        countries = [
            "US",
            "CA",
            "BE",
            "FR",
            "DE",
            "HK",
            "IE",
            "IT",
            "JP",
            "KW",
            "CN",
            "MX",
            "NL",
            "QA",
            "SA",
            "ES",
            "AE",
            "GB",
            "KR",
            "SE",
            "AT",
            "PL",
        ]

        template = "https://www.hollisterco.com/api/ecomm/h-us/storelocator/search?country={country}"

        for country in countries:
            url = template.format(country=country)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        data = response.json()

        for row in data["physicalStores"]:
            properties = {
                "ref": row["storeNumber"],
                "name": row["name"],
                "country": row["country"],
                "state": row["stateOrProvinceName"],
                "city": row["city"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "phone": row["telephone"],
                "addr_full": row["addressLine"][0],
                "postcode": row["postalCode"],
            }

            yield GeojsonPointItem(**properties)
