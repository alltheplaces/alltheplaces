from scrapy import Selector
from scrapy.http import Request
from scrapy.spiders import Spider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BucoNAZASpider(Spider):
    name = "buco_na_za"
    item_attributes = {"brand": "BUCO", "brand_wikidata": "Q116771533"}
    allowed_domains = ["buco.co.za"]
    start_urls = ["https://www.buco.co.za/find-a-store"]
    skip_auto_cc_domain = True
    no_refs = True

    def parse(self, response):
        for link in response.xpath('.//a[contains(@class, "product-item-link")]/@href').getall():
            yield Request(url=link, callback=self.parse_store)

    def parse_store(self, response):
        item = Feature()
        item["branch"] = response.xpath('.//span[@data-ui-id="page-title-wrapper"]/text()').get()
        item["addr_full"] = clean_address(response.xpath('.//div[@class="shop-contact-address"]/text()').getall())
        item["phone"] = response.xpath(
            './/div[contains(@class, "phone-number")]/.//a[contains(@href, "tel:")]/@href'
        ).get()
        extract_google_position(item, response)
        item["opening_hours"] = OpeningHours()
        for day in response.xpath(
            './/div[contains(@class, "shop-opening-times")]//span[contains(@class, "day-name")]'
        ).getall():
            day_hours = Selector(text=day).xpath("string(.)").get().strip()
            if "closed" in day_hours.lower():
                item["opening_hours"].set_closed(day_hours.split(" ")[0])
            else:
                item["opening_hours"].add_ranges_from_string(day_hours)
        yield item
