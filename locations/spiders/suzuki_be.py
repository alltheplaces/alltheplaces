import scrapy
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
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

            infowindow_selector = Selector(text=row.get("infowindow_content"))
            item["phone"] = infowindow_selector.xpath("//p//a/text()").get()
            item["street_address"] = infowindow_selector.xpath("//div/p/text()[1]").get().strip()

            city_codepost = infowindow_selector.xpath("//div/p/text()[2]").get().strip()
            item["postcode"] = city_codepost.split(" ")[0]
            item["city"] = city_codepost.split(" ")[1]

            item["lat"] = row.get("latitude")
            item["lon"] = row.get("longitude")
            apply_category(Categories.SHOP_CAR, item)

            yield item
