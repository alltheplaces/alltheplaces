from urllib.parse import urljoin

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class TvoeRUSpider(scrapy.Spider):
    name = "tvoe_ru"
    start_urls = ["https://tvoe.ru/contacts/"]
    item_attributes = {
        "brand": "ТВОЕ",
        "brand_wikidata": "Q110034939",
    }

    def parse(self, response):
        pois = response.xpath('//div[@class="contacts-stores shops-list1"]/div[@class="item bordered box-shadow wti"]')
        for poi in pois:
            item = Feature()
            slug = poi.xpath('.//div[contains(@class, "title")]/a/@href').get()
            item["ref"] = item["website"] = urljoin(response.url, slug)
            item["phone"] = poi.xpath('.//div[contains(@class,"phone")]/a/text()').get()
            item["email"] = poi.xpath('.//div[contains(@class,"email")]/a/text()').get()
            coords = poi.xpath(".//span/@data-coordinates").get(default="").split(",")
            if len(coords) == 2:
                item["lat"] = coords[0]
                item["lon"] = coords[1]
            item["addr_full"] = poi.xpath('.//div[contains(@class, "title")]/a/text()').get(default="").strip()
            self.parse_hours(item, poi)
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item

    def parse_hours(self, item, poi):
        if schedule := poi.xpath('.//div[@class="schedule"]/span/text()').get():
            try:
                oh = OpeningHours()
                open, close = schedule.replace(" ", "").split("-")
                oh.add_days_range(DAYS, open, close)
                item["opening_hours"] = oh
            except Exception as e:
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/fail")
                self.logger.warning(f"Failed to parse hours: {schedule}, {e}")
