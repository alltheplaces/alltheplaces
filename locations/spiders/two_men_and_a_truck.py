import scrapy

from locations.items import Feature


class TwoMenAndATruckSpider(scrapy.Spider):
    name = "two_men_and_a_truck"
    item_attributes = {"brand": "Two Men and a Truck", "brand_wikidata": "Q7859087"}
    allowed_domains = ["twomenandatruck.com", "twomenandatruck.ca"]

    def start_requests(self):
        urls = [
            "https://twomenandatruck.com/feed/locations",
            "https://twomenandatruck.ca/feed/locations",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = response.json()
        for place in data["locations"]:
            properties = {
                "name": place["location_name"],
                "ref": place["location_id"],
                "addr_full": place["address_street"],
                "city": place["address_city"],
                "state": place["address_state_province"],
                "postcode": place["address_postal_code"],
                "country": place["address_country"],
                "phone": place["phone_office"],
                "website": place["web_display_url"],
                "lat": place["coordinates_latitude"],
                "lon": place["coordinates_longitude"],
            }

            yield Feature(**properties)
