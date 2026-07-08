from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FHindsGBSpider(Spider):
    name = "f_hinds_gb"
    item_attributes = {"brand": "F.Hinds", "brand_wikidata": "Q5423915"}
    start_urls = [
        "https://www.fhinds.co.uk/store-locator?view_all=true",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = response.xpath('//*[@class="store-title"]//@href').getall()
        for location in locations:
            url = urljoin("https://www.fhinds.co.uk", location)
            yield scrapy.Request(url=url, callback=self.parse_location)

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get().replace("F.Hinds the Jewellers, ", "")
        item["addr_full"] = merge_address_lines(
            response.xpath('//*[@class="container store-details-template"]/div/div/div/div/p[1]/text()').getall()
        )
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        oh = OpeningHours()
        item["opening_hours"] = oh
        hours_text = " ".join(
            response.xpath(
                "//h3[normalize-space()='Opening Hours']/following-sibling::p[1]//text()[normalize-space()]"
            ).getall()
        )
        oh.add_ranges_from_string(hours_text)
        item["opening_hours"] = oh
        yield item
