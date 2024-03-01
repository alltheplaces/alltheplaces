from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_phone


class LesliesPoolmartUSSpider(SitemapSpider):
    name = "leslies_poolmart_us"
    item_attributes = {"brand": "Leslie's Poolmart", "brand_wikidata": "Q6530568"}
    sitemap_urls = ["https://lesliespool.com/robots.txt"]
    sitemap_rules = [("/location/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.xpath("//a[@data-store-id]/@data-store-id").get()
        item["lat"] = response.xpath("//a[@data-store-latitude]/@data-store-latitude").get()
        item["lon"] = response.xpath("//a[@data-store-longitude]/@data-store-longitude").get()
        item["branch"] = response.xpath("//h1/text()").get()
        item["website"] = response.url
        extract_phone(item, response)

        item["addr_full"] = merge_address_lines(
            response.xpath('//h5[contains(@class, "store-detail-address")]/span/text()').getall()
        )

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//div[contains(./h5/text(), "Hours")]/div/p/text()').getall():
            day, times = rule.split(" : ")
            if times == "Closed":
                continue
            item["opening_hours"].add_range(day, *times.split(" - "), "%I %p")

        yield item
