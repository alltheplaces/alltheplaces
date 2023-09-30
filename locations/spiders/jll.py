import scrapy

from locations.items import Feature


class JllSpider(scrapy.Spider):
    name = "jll"
    item_attributes = {"brand": "JLL", "brand_wikidata": "Q1703389"}
    allowed_domains = ["jll.com"]

    def start_requests(self):
        base_url = "https://www.us.jll.com/bin/jll/search?q=locations&currentPage=/content/jll-dot-com/countries/amer/us/en/locations&top=100&p={page}&contentTypes=Location"
        pages = ["1", "2", "3", "4"]

        for page in pages:
            url = base_url.format(page=page)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = response.json()

        for place in data["azureSearch"]["value"]:
            properties = {
                "ref": place["id"],
                "name": place["title"],
                "street_address": place["streetAddress"],
                "city": place["city"],
                "state": place["stateProvince"],
                "postcode": place["postalCode"],
                "lat": place["latitude"],
                "lon": place["longitude"],
                "phone": place["telephoneNumber"],
                "website": place["cityPageLink"],
            }

            if "https://www.us.jll.com/en/locations" in properties["website"]:
                properties["country"] = "US"

            yield Feature(**properties)
