from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class BananaTreeGBSpider(SitemapSpider):
    name = "banana_tree_gb"
    item_attributes = {"brand": "Banana Tree", "brand_wikidata": "Q123013837"}
    sitemap_urls = ["https://bananatree.co.uk/sitemap.xml"]
    sitemap_rules = [("/restaurants/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@class="about-contact-info"]/h1/text()').get()
        item["addr_full"] = response.xpath('//*[@class="address"]/text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        oh = OpeningHours()
        for day_time in response.xpath('//*[@class="opening-hours-day"]'):
            day = day_time.xpath(".//span").xpath("normalize-space()").get()
            open_time, close_time = day_time.xpath(".//span[2]").xpath("normalize-space()").get().split(" - ")
            oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        yield item
