import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.searchable_points import open_searchable_points


class CheddarsScratchKitchenSpider(scrapy.Spider):
    name = "cheddars_scratch_kitchen"
    allowed_domains = ["cheddars.com"]
    item_attributes = {
        "brand": "Cheddar's Scratch Kitchen",
        "brand_wikidata": "Q5089187",
    }

    def start_requests(self):
        url = "https://www.cheddars.com/web-api/restaurants"

        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            next(points)  # Ignore the header
            for point in points:
                _, lat, lon = point.strip().split(",")
                formdata = {
                    "geoCode": lat + "," + lon,
                    "resultsPerPage": "500",
                    "resultsOffset": "0",
                    "displayDistance": "false",
                    "locale": "en_US",
                }

                yield scrapy.http.FormRequest(
                    url,
                    self.parse,
                    method="POST",
                    formdata=formdata,
                )

    def parse(self, response):
        data = response.json()

        try:
            for place in data["successResponse"]["locationSearchResult"]["Location"]:
                properties = {
                    "ref": place["restaurantNumber"],
                    "name": place["restaurantName"],
                    "street_address": merge_address_lines([place["AddressOne"], place["AddressTwo"]]),
                    "city": place["city"],
                    "state": place["state"],
                    "postcode": place["zip"],
                    "country": place["country"],
                    "lat": place["latitude"],
                    "lon": place["longitude"],
                    "phone": place["phoneNumber"],
                    "website": response.url,
                }

                yield Feature(**properties)
        except:
            pass
