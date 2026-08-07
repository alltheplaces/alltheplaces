import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class UclaHealthSpider(scrapy.Spider):
    name = "ucla_health"
    item_attributes = {"operator": "UCLA Health", "operator_wikidata": "Q18394900"}
    allowed_domains = ["maps.uclahealth.org"]
    start_urls = ["https://maps.uclahealth.org/googlemaps/json/clinicdatabase.json"]

    def parse(self, response):
        result = response.json()

        for place in result:
            properties = {
                "ref": str(place["UID"]),
                "name": place["Custom - Internal Name"],
                "street_address": place["Address1"],
                "city": place["City"],
                "state": "CA",
                "postcode": str(place["Zip"]),
                "country": "US",
                "lat": place["Latitude"],
                "lon": place["Longitude"],
                "phone": place["Phone"],
                "website": place["Website"],
            }

            item = Feature(**properties)
            apply_category(Categories.CLINIC, item)
            yield item
