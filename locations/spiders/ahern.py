import scrapy

from locations.items import Feature


class AhernSpider(scrapy.Spider):
    name = "ahern"
    item_attributes = {"brand": "Ahern Rentals", "brand_wikidata": "Q114487657"}
    allowed_domains = ["ahern.com"]
    start_urls = (
        "https://www.ahern.com/themes/theaherns/js/plugins/storeLocator/data/locations.json?formattedAddress=&boundsNorthEast=&boundsSouthWest=",
    )

    def parse(self, response):
        data = response.json()

        for i in data:
            properties = {
                "ref": i.get("name"),
                "name": i.get("name"),
                "street_address": i.get("address") + i.get("address2"),
                "city": i.get("city"),
                "state": i.get("state"),
                "postcode": i.get("postal"),
                "country": "US",
                "phone": i.get("phone"),
                "lat": i.get("lat"),
                "lon": i.get("lng"),
            }

            yield Feature(**properties)
