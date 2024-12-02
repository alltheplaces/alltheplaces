from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BabyCityZASpider(CrawlSpider):
    name = "baby_city_za"
    item_attributes = {"brand": "Baby City", "brand_wikidata": "Q116732888"}
    allowed_domains = ["www.babycity.co.za"]
    start_urls = ["https://www.babycity.co.za/find-a-store"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[contains(@class, "store-info")]'), "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url,
            "branch": response.xpath('//h1[contains(@class, "store-title")]/span/text()')
            .get()
            .removeprefix("Baby City "),
            "addr_full": merge_address_lines(
                response.xpath('//div[contains(@class, "shop-contact-address")]/text()').getall()
            ),
            "phone": response.xpath('//div[contains(@class, "phone-number")]/div/span/text()').get(),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_google_position(properties, response)
        apply_category(Categories.SHOP_BABY_GOODS, properties)
        hours_text = " ".join(
            filter(
                None,
                map(
                    str.strip,
                    response.xpath(
                        '(//div[@class="product info detailed"]/div[contains(@class, "store-accordion-container")]/div[@class="accordion-item"])[1]/div[contains(@class, "accordion-content")]/span[contains(@class, "day-name")]//text()'
                    ).getall(),
                ),
            )
        )
        properties["opening_hours"].add_ranges_from_string(hours_text)
        yield Feature(**properties)
