import json
from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class DunhamsSportsUSSpider(Spider):
    name = "dunhams_sports_us"
    item_attributes = {"brand": "Dunham's Sports", "brand_wikidata": "Q5315238"}
    allowed_domains = ["www.dunhamssports.com"]
    start_urls = ["https://www.dunhamssports.com/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for city_id in response.xpath('//*[@name="store-locator-store-id"]//@value').getall():
            if city_id:
                yield scrapy.Request(
                    url=f"https://www.dunhamssports.com/find-stores/?storeId={city_id}", callback=self.parse_details
                )

    def parse_details(self, response):
        for lat_lon_data in json.loads(response.xpath('//*[@id="coordinates-data"]/@value').get()):
            location_id = lat_lon_data["num"]
            for location in response.xpath(f'//*[@id="map-info-{location_id}"]'):
                item = Feature()
                item["lat"] = lat_lon_data["lat"]
                item["lon"] = lat_lon_data["lng"]
                item["branch"] = location.xpath('.//*[@class="fs-13px mb-2 fw-medium"]/div[1]/text()').get()
                item["street_address"] = location.xpath('.//*[@class="fs-13px mb-2 fw-medium"]/div[2]/text()').get()
                item["city"] = location.xpath('.//*[@class="fs-13px mb-2 fw-medium"]//span[1]/text()').get()
                item["state"] = location.xpath('.//*[@class="fs-13px mb-2 fw-medium"]//span[2]/text()').get()
                item["postcode"] = location.xpath('.//*[@class="fs-13px mb-2 fw-medium"]//span[3]/text()').get()
                item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
                item["ref"] = item["website"] = urljoin(
                    "https://www.dunhamssports.com/", location.xpath(".//span//@href").get().replace(" ", "")
                )
                try:
                    oh = OpeningHours()
                    for day_time in location.xpath('.//*[@class="store-hours-table fs-13px mb-2"]//tr'):
                        oh.add_ranges_from_string("".join(day_time.xpath(".//td//text()").getall()))
                    item["opening_hours"] = oh
                except:
                    pass
                yield item
