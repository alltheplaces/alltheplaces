from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

# from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class HaysTravelGBSpider(Spider):
    name = "hays_travel_gb"
    item_attributes = {"brand": "Hays Travel", "brand_wikidata": "Q70250954"}
    start_urls = ["https://www.haystravel.co.uk/umbraco/api/branches/getbranchlocatorcontent"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//li[contains(@class,"py-8")]'):
            item = Feature()
            item["ref"] = url = location.xpath('.//a[contains(@href,"branches")]/@href').get()
            item["website"] = urljoin("https://www.haystravel.co.uk/", url)
            item["name"] = location.xpath("@data-branch-title").get()
            coords = location.xpath("@data-branch-lat-lng").get()
            item["lat"], item["lon"] = [c.strip() for c in coords.split(",")]
            item["phone"] = location.xpath('.//a[contains(@href, "tel:")]/@href').get().replace("tel:", "")
            item["addr_full"] = merge_address_lines(
                location.xpath('.//div[contains(@class,"rich-text")]//p//text()').getall()
            )
            yield item
