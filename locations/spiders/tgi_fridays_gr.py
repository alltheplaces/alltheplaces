from typing import Any

import scrapy
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.items import Feature


class TgiFridaysGRSpider(scrapy.Spider):
    name = "tgi_fridays_gr"
    item_attributes = {"brand": "TGI Fridays", "brand_wikidata": "Q1524184"}
    start_urls = ["https://www.fridays.gr/en/restaurants/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for restaurant in response.xpath('//*[@id = "map-category-locations"]//li'):
            item = Feature()
            item["name"] = restaurant.xpath(".//h4/text()").get()
            item["addr_full"] = restaurant.xpath(".//p/text()").get()
            item["phone"] = restaurant.xpath('.//*[contains(@href,"tel:")]//text()').get()
            item["email"] = restaurant.xpath('.//*[contains(@href,"mailto:")]/text()').get()
            item["ref"] = restaurant.xpath(".//@data-id").get()
            item["website"] = "https://www.fridays.gr/"
            extract_google_position(item, restaurant)
            yield item
