import json

import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class VolvoBeSpider(scrapy.Spider):
    name = "volvo_be"
    item_attributes = {"brand": "Volvo", "brand_wikidata": "Q163810"}
    allowed_domains = ["volvocars.com"]
    start_urls = ["https://www.volvocars.com/fr-be/dealers/distributeurs"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        data_raw = response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get()
        locator = json.loads(data_raw)["props"]["pageProps"]["retailers"]
        for row in locator:
            item = Feature()
            item["ref"] = row.get("partnerId")
            item["name"] = row.get("name")
            item["street_address"] = row.get("addressLine1")
            item["postcode"] = row.get("postalCode")
            item["city"] = row.get("city")
            item["lat"] = row.get("latitude")
            item["lon"] = row.get("longitude")
            item["country"] = row.get("country")
            item["phone"] = row.get("phoneNumbers", {}).get("retailer")
            item["website"] = row.get("url")
            item["email"] = row.get("generalContactEmail")

            yield item
