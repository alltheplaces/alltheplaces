from typing import Iterable

from parsel import Selector
from scrapy import Spider
from scrapy.http import Response

from locations.hours import CLOSED_NO, DAYS_NO, OpeningHours
from locations.items import Feature


class PizzabakerenNOSpider(Spider):
    name = "pizzabakeren_no"
    item_attributes = {"brand": "Pizzabakeren", "brand_wikidata": "Q11995777"}
    start_urls = ["https://www.pizzabakeren.no/box_search.php?search=#"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in response.xpath('//div[@class="bs_row"]'):
            name = store.xpath(".//h3/text()").get("").strip()

            item = Feature()

            item["ref"] = store.xpath('.//a[contains(@class, "find_marker")]/@data-map').get()
            item["branch"] = name
            item["lat"] = store.xpath('.//a[contains(@class, "find_marker")]/@data-lat').get()
            item["lon"] = store.xpath('.//a[contains(@class, "find_marker")]/@data-lng').get()
            item["phone"] = store.xpath('.//h3//span[@class="ib"]/span/text()').get()

            self.parse_address(store, item)

            hours_div = store.xpath('.//div[@class="bs_days"]//div[@class="ib"]')
            if hours_div:
                hours_text = hours_div.xpath("string(.)").get()
                if hours_text:
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_NO, closed=CLOSED_NO)

            yield item

    def parse_address(self, store: Selector, item: Feature) -> None:
        address_raw = store.xpath(".//h5/text()").get()
        if address_raw:
            address_parts = address_raw.strip().split(",")
            if len(address_parts) >= 2:
                item["street_address"] = address_parts[0].strip()
                item["city"] = address_parts[1].strip().split("(")[0].strip()
            elif len(address_parts) == 1:
                item["street_address"] = address_parts[0].strip()
