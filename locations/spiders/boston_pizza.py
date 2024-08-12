import scrapy

from locations.items import Feature


class BostonPizzaSpider(scrapy.Spider):
    name = "boston_pizza"
    item_attributes = {
        "brand": "Boston Pizza",
        "brand_wikidata": "Q894578",
    }
    allowed_domains = ["bostonpizza.com"]
    start_urls = [
        "https://bostonpizza.com/en/locations.html",
    ]

    def parse(self, response):
        url = response.css(".restaurant-locator").attrib["data-res-path"] + ".getAllRestaurants.json"
        yield response.follow(url, callback=self.parse_restaurants)

    def parse_restaurants(self, response):
        for store in response.json()["map"]["response"]:
            properties = {
                "phone": store["restaurantPhoneNumber"],
                "country": store["country"],
                "ref": store["identifier"],
                "street_address": store["address"],
                "city": store["city"],
                "lat": store["latitude"],
                "postcode": store["postalCode"],
                "website": response.urljoin(store["restaurantPage"]),
                "state": store["province"],
                "name": store["restaurantName"],
                "lon": store["longitude"],
            }
            yield Feature(**properties)
