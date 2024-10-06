import re

import scrapy
from scrapy.linkextractors import LinkExtractor

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PizzaHutLUSpider(scrapy.Spider):
    name = "pizza_hut_lu"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://restaurants.pizzahut.lu"]

    def parse(self, response, **kwargs):
        for link in LinkExtractor(restrict_xpaths='//*[@id="restaurant_submenu"]').extract_links(response):
            parsed_link = re.sub(r"/restaurant/(.+)", r"/pages/restaurant.php?attr=\1", link.url)
            yield response.follow(parsed_link, callback=self.parse_restaurant, cb_kwargs=dict(website=link.url))

    def parse_restaurant(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = kwargs.get("website")
        address = response.xpath('//*[@id="left_bar_content"]//b/text()').getall()
        item["name"] = "Pizza Hut " + address[0].title()
        item["addr_full"] = clean_address(address[1:]).strip(", Tél.")
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get().replace("tel:", "")
        if map_data := response.xpath('//script[contains(text(), "google.maps.LatLng")]/text()').get():
            item["lat"], item["lon"] = re.search(r"LatLng\(([-\d.]+)\s*,\s*([-\d.]+)\)", map_data).groups()
        apply_category(Categories.RESTAURANT, item)
        yield item
