import scrapy

from locations.items import Feature, SocialMedia, set_social_media


class CrunchFitnessSpider(scrapy.Spider):
    name = "crunch_fitness"
    item_attributes = {"brand": "Crunch Fitness", "brand_wikidata": "Q5190093"}
    allowed_domains = ["crunch.com"]
    start_urls = ["https://www.crunch.com/load-clubs"]

    def parse(self, response):
        for club in response.json()["clubs"]:
            properties = {
                "branch": club["name"],
                "ref": club["id"],
                "street_address": club["address"]["address_1"],
                "city": club["address"]["city"],
                "state": club["address"]["state"],
                "postcode": club["address"]["zip"],
                "country": club["address"]["country_code"],
                "phone": club.get("phone"),
                "email": club.get("email"),
                "facebook": club.get("facebook_url"),
                "website": "https://www.crunch.com/locations/" + club["slug"],
                "lat": float(club["latitude"]),
                "lon": float(club["longitude"]),
            }
            item = Feature(**properties)
            set_social_media(item, SocialMedia.INSTAGRAM, club.get("instagram_url"))

            yield item
