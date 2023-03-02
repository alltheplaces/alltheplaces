import json

import scrapy
from scrapy.selector import Selector

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SuzukiBeSpider(scrapy.Spider):
    name = "suzuki_be"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}
    allowed_domains = ["suzuki.be"]
    start_urls = ["https://www.suzuki.be/fr/ajax/dealers"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        for key, row in response.json().get("map_data", {}).get("locations").items():
            item = Feature()
            item["ref"] = key
            item["name"] = row.get("title")
            item["street_address"] = (
                Selector(text=row.get("infowindow_content")).xpath("//div/p/text()[1]").get().strip()
            )
            city_codepost = Selector(text=row.get("infowindow_content")).xpath("//div/p/text()[2]").get().strip()
            item["postcode"] = city_codepost.split(" ")[0]
            item["city"] = city_codepost.split(" ")[1]
            item["lat"] = row.get("latitude")
            item["lon"] = row.get("longitude")
            item["phone"] = Selector(text=row.get("infowindow_content")).xpath("//p//a/text()").get()

            yield item
