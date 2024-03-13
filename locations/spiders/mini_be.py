import scrapy
import xmltodict

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class MiniBESpider(scrapy.Spider):
    name = "mini_be"
    item_attributes = {
        "brand": "Mini",
        "brand_wikidata": "Q116232",
    }
    allowed_domains = ["mini.be"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://c2b-services.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/-/pois?category=MI&maxResults=2000&showAll=true&country=BE"
    ]

    def parse(self, response):
        if "xml" in str(response.headers.get("content-type")):
            data = xmltodict.parse(response.body)
            pois = data.get("result", {}).get("data", {}).get("pois", {}).get("poi")
        else:
            pois = response.json().get("status", {}).get("data", {}).get("pois")
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
