import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class MiniSpider(scrapy.Spider):
    name = "mini_be"
    item_attributes = {
        "brand": "Mini",
        "brand_wikidata": "Q116232",
    }
    allowed_domains = ["mini.be"]
    user_agent = BROWSER_DEFAULT
    start_urls = [
        "https://www.mini.be/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/BE/pois?brand=MINI&cached=off&category=MI&country=BE&language=nl&lat=0&lng=0&maxResults=700&showAll=true&unit=km"
    ]

    def parse(self, response):
        pois = response.json().get("data", {}).get("pois")
        for row in pois:
            item = Feature()
            item["ref"] = row.get("key")
            item["name"] = row.get("name")
            item["street_address"] = row.get("street")
            item["city"] = row.get("city")
            item["postcode"] = row.get("postalCode")
            item["lat"] = row.get("lat")
            item["lon"] = row.get("lng")
            item["country"] = row.get("countryCode")
            item["phone"] = row.get("attributes", {}).get("phone")
            item["email"] = row.get("attributes", {}).get("mail")
            item["website"] = row.get("attributes", {}).get("homepage")

            yield item
