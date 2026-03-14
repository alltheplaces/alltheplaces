import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.ikea import IkeaSpider


class IkeaTRSpider(Spider):
    name = "ikea_tr"
    item_attributes = IkeaSpider.item_attributes
    start_urls = ["https://www.ikea.com.tr/magazalar"]
    HOURS_PATTERN = re.compile(r"Haftanın\s+7\s+[gG]ün[uü]:\s*(\d{1,2}[.:]\d{2})\s*-\s*(\d{1,2}[.:]\d{2})")

    def parse(self, response: Response) -> Iterable[Request]:
        for store in response.xpath('//div[@class="malls-city-item"]'):
            item = Feature()
            item["ref"] = store.xpath(".//h4/a/@href").get().split("/")[-1]
            item["branch"] = store.xpath(".//h4/a/text()").get().replace("IKEA", "")
            item["website"] = response.urljoin(store.xpath(".//h4/a/@href").get())

            # Inaccurate coordinates, more accurate ones are extracted from the store page, but still not ideal data.
            # lat = store.xpath(".//@data-latitude").get()
            # lon = store.xpath(".//@data-longitude").get()

            addr_parts = store.xpath(".//p//text()").getall()
            item["addr_full"] = merge_address_lines(addr_parts)

            yield Request(
                url=item["website"],
                callback=self.parse_store,
                meta={"item": item},
            )

    def parse_store(self, response: Response) -> Iterable[Feature]:
        store = response.meta["item"]
        extract_google_position(store, response)

        if restaurant := self.parse_restaurant(response, store):
            apply_category(Categories.FAST_FOOD, restaurant)
            yield restaurant

        store_hours = response.xpath('//h3[contains(text(), "Çalışma Saatleri")]/following-sibling::p//text()').getall()
        store["opening_hours"] = self.parse_hours(store_hours, store["ref"])
        apply_category(Categories.SHOP_FURNITURE, store)
        yield store

    def parse_restaurant(self, response: Response, item: Feature) -> Feature | None:
        restaurant_hours_section = response.xpath(
            '//h3[contains(text(), "Restoranı Çalışma Saatleri")]/following-sibling::p//text()'
        ).getall()
        if restaurant_hours_section:
            ref = f"{item['ref']}-restaurant"
            restaurant_hours = self.parse_hours(restaurant_hours_section, ref)
            if restaurant_hours:
                restaurant = item.deepcopy()
                restaurant["ref"] = ref
                restaurant["name"] = "IKEA İsveç Restoranı"
                restaurant["opening_hours"] = restaurant_hours
                return restaurant
        return None

    def parse_hours(self, hours_lines: Any, ref: str) -> OpeningHours | None:
        try:
            for line in hours_lines:
                line = line.strip()
                if match := self.HOURS_PATTERN.search(line):
                    open_time = match.group(1).replace(".", ":")
                    close_time = match.group(2).replace(".", ":")
                    oh = OpeningHours()
                    oh.add_days_range(DAYS, open_time, close_time)
                    return oh
        except Exception as e:
            self.logger.error(f"Error parsing hours for {ref}: {e}")
            self.crawler.stats.inc_value("atp/hours/failed")
        return None
