from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class CornerstoneHealthcareGroupUSSpider(CrawlSpider):
    name = "cornerstone_healthcare_group_us"
    item_attributes = {"brand": "Cornerstone Healthcare Group"}
    start_urls = ["https://cornerstonehospitals.com/locations"]
    rules = [Rule(LinkExtractor(r"https://www.cornerstonehospitals.com/locations/[^/]+/[^/]+$"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = self.item_attributes["brand"]
        item["branch"] = response.xpath("//h1//text()").get()
        item["addr_full"] = response.xpath('//*[@id="text-cf7b8a0952"]//p//text()').get()
        item["website"] = item["ref"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.HOSPITAL, item)
        yield item
