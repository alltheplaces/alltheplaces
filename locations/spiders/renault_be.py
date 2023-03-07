import scrapy

from locations.items import Feature


class MiniSpider(scrapy.Spider):
    name = "renault_be"
    item_attributes = {
        "brand": "Renault",
        "brand_wikidata": "Q98584518",
    }
    allowed_domains = ["renault.be"]
    start_urls = [
        "https://fr.renault.be/wired/commerce/v1/dealers/locator?lat=50.38868024865795&lon=5.83373975753608&country=be&language=fr&filters=renault.blacklisted%3D%3Dfalse%3Brenault.receiveLead%3D%3Dtrue&count=5000000&dealerAttachment=true"
    ]

    def parse(self, response):
        for row in response.json():
            item = Feature()
            item["ref"] = row.get("birId")
            item["name"] = row.get("name")
            item["street_address"] = row.get("streetAddress")
            item["city"] = row.get("locality")
            item["postcode"] = row.get("postalCode")
            item["lat"] = row.get("geolocalization", {}).get("lat")
            item["lon"] = row.get("geolocalization", {}).get("lon")
            item["country"] = row.get("country")
            item["phone"] = row.get("telephone", {}).get("value")

            yield item
