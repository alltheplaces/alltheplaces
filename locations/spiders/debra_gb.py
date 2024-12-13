from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class DebraGBSpider(SitemapSpider):
    name = "debra_gb"
    item_attributes = {"brand": "Debra", "brand_wikidata": "Q104535435"}
    sitemap_urls = ["https://www.debra.org.uk/sitemap.xml"]
    sitemap_rules = [(r"/charity-shop/\w+", "parse")]
    sitemap_follow = ["shop"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get()
        item["addr_full"] = clean_address(response.xpath('//*[contains(@class,"details-address")]/text()').get())
        item["phone"] = response.xpath('//*[contains(@class,"details-phone")]/text()').get()
        item["email"] = response.xpath('//*[contains(@class,"details-email")]/text()').get()
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["ref"] = item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        day_time_string = response.xpath('//*[@class="single-shop__details-opening-times"]/text()').get()
        item["opening_hours"].add_ranges_from_string(day_time_string)
        yield item
