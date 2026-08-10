from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Request

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class CrustAUSpider(Spider):
    name = "crust_au"
    item_attributes = {"brand": "Crust", "brand_wikidata": "Q100792715"}
    allowed_domains = ["www.crust.com.au"]
    requires_proxy = True
    start_urls = ["https://www.crust.com.au/stores/stores_for_map_markers.json?catering_active=false"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if "test" in location["name"].lower():
                continue
            item = DictParser.parse(location)
            item["lat"], item["lon"] = location["location"].split(",", 1)
            item.pop("addr_full", None)
            item["street_address"] = clean_address([location["address"], location["address2"]])
            item["postcode"] = str(item.get("postcode", ""))
            yield Request(
                url="https://www.crust.com.au/stores/{}/store_online?&context=locator".format(location["id"]),
                meta={"item": item},
                callback=self.add_store_details,
            )

    def add_store_details(self, response):
        item = response.meta["item"]
        item["website"] = "https://www.crust.com.au" + response.xpath('//div[@class="store_container"]/a/@href').get()
        item["addr_full"] = " ".join(
            filter(None, map(str.strip, response.xpath('//div[@class="store_container"]/p[1]/text()').getall()))
        )
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get("").replace("tel:", "")
        item["email"] = response.xpath('//a[contains(@href, "mailto:")]/@href').get("").replace("mailto:", "")
        item["opening_hours"] = OpeningHours()
        try:
            self._parse_hours(response, item)
        except Exception:
            self.logger.warning("Failed to parse hours for %s", item.get("name"))
        yield item

    @staticmethod
    def _parse_hours(response, item):
        for row in response.xpath('//div[@class="opening-hours"]/table/tbody/tr'):
            day = row.xpath("td[1]/text()").get("").strip().split(",", 1)[0]
            lunch = row.xpath("td[2]/text()").get("").strip()
            dinner = row.xpath("td[3]/text()").get("").strip()
            for time_range in [lunch, dinner]:
                if not time_range or time_range == "N/A":
                    continue
                item["opening_hours"].add_ranges_from_string(f"{day}: {time_range}")
