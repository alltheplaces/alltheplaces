import scrapy

from locations.items import Feature


class CornerstoneHealthcareGroupSpider(scrapy.Spider):
    name = "cornerstone_healthcare_group"
    item_attributes = {"brand": "Cornerstone Healthcare Group"}
    allowed_domains = ["chghospitals.com"]
    start_urls = [
        "https://www.chghospitals.com/wp-json/wp/v2/location?per_page=100",
    ]

    def parse(self, response):
        data = response.json()

        for i, item in enumerate(data):
            properties = {
                "name": item["title"]["rendered"],
                "street_address": item["acf"]["address"],
                "city": item["acf"]["city"],
                "state": item["acf"]["state"],
                "postcode": item["acf"]["zip"],
                "country": "US",
                "ref": item["link"],
                "website": item["link"],
                "phone": item["acf"]["phone"],
                "lat": item["acf"]["latitude"],
                "lon": item["acf"]["longitude"],
            }
            yield Feature(**properties)
