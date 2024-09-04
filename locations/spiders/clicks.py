from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import CrawlSpider, SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class ClicksSpider(CrawlSpider, SitemapSpider):
    name = "clicks"
    item_attributes = {"brand": "Clicks", "brand_wikidata": "Q62563622"}
    allowed_domains = ["clicks.co.za"]
    sitemap_urls = ["https://clicks.co.za/sitemap.xml"]
    sitemap_rules = [(r"/store/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["lat"] = response.xpath('.//div[contains(@class, "map active")]/@data-latitude').get()
        item["lon"] = response.xpath('.//div[contains(@class, "map active")]/@data-longitude').get()
        item["website"] = response.url
        item["ref"] = item["website"].split("/")[-1]
        item["branch"] = response.xpath(".//h1/text()").get()
        item["addr_full"] = response.xpath(
            './/div[contains(@class, "title-bar")]/p/strong[contains(text(), "Address")]/../span/text()'
        ).get()
        item["phone"] = "; ".join(response.xpath('.//span[contains(@class, "phone_num")]/text()').getall())
        item["opening_hours"] = OpeningHours()
        for day in response.xpath('.//div[contains(@class, "openingHoursWrap")]/.//dl').getall():
            item["opening_hours"].add_ranges_from_string(Selector(text=day).xpath("string(.//dl)").get())
        yield item
