from typing import Any
from urllib import parse

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature


class PizzaHutLUSpider(SitemapSpider):
    name = "pizza_hut_lu"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    sitemap_urls = ["https://restaurants.pizzahut.lu/restaurants-sitemap.xml"]
    sitemap_rules = [(r"restaurants.pizzahut.lu/de/restaurants/[-\w]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_info = response.xpath('//*[@class="map-info"]')
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = location_info.xpath("./h3/text()").get("").removeprefix("Pizza Hut ")
        item["addr_full"] = location_info.xpath('.//*[@class="address"]/text()').get()
        if map_url := response.xpath("//@data-src-cmplz").get():
            item["lat"], item["lon"] = url_to_coords(map_url)
        item["phone"] = parse.unquote(response.xpath('//a[contains(@href,"tel:")]/@href').get(""))
        item["email"] = response.xpath('//a[contains(@href,"mailto:")]/@href').get()
        apply_category(Categories.RESTAURANT, item)
        yield item
