from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BabyCityZASpider(CrawlSpider):
    name = "baby_city_za"
    item_attributes = {"brand": "Baby City", "brand_wikidata": "Q116732888", "extras": Categories.SHOP_BABY_GOODS.value}
    allowed_domains = ["www.babycity.co.za"]
    start_urls = ["https://www.babycity.co.za/find-a-store"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[contains(@class, "store-info")]'), "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url,
            "name": response.xpath('//h1[contains(@class, "store-title")]/span/text()').get(),
            "addr_full": merge_address_lines(response.xpath('//div[contains(@class, "shop-contact-address")]/text()').getall()),
            "phone": response.xpath('//div[contains(@class, "phone-number")]/div/span/text()').get(),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        hours_text = " ".join(filter(None, map(str.strip, response.xpath('(//div[@class="product info detailed"]/div[contains(@class, "store-accordion-container")]/div[@class="accordion-item"])[1]/div[contains(@class, "accordion-content")]/span[contains(@class, "day-name")]//text()').getall())))
        properties["opening_hours"].add_ranges_from_string(hours_text)
        yield Feature(**properties)
