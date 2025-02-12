import re

from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.ocean_basket_1 import OCEAN_BASKET_SHARED_ATTRIBUTES


class OceanBasket2Spider(SitemapSpider):
    name = "ocean_basket_2"
    item_attributes = OCEAN_BASKET_SHARED_ATTRIBUTES
    sitemap_urls = [
        "https://saudiarabia.oceanbasket.com/robots.txt",
        "https://kazakhstan.oceanbasket.com/robots.txt",
        "https://ghana.oceanbasket.com/robots.txt",
    ]
    sitemap_rules = [
        (r"^https:\/\/.+\.oceanbasket\.com\/our-restaurants\/.+$", "parse"),
    ]

    def parse(self, response):
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = (
            response.xpath('.//div[@class="page_title"]/h2/text()')
            .get()
            .replace(self.item_attributes["brand"], "")
            .strip()
        )
        item["phone"] = response.xpath('.//p[@class="desc"][1]/text()').get().removeprefix(" : ")
        item["addr_full"] = response.xpath('.//p[@class="desc"][3]/text()').get().removeprefix(" : ")
        extract_google_position(item, response)

        item["opening_hours"] = OpeningHours()
        for times in response.xpath('.//p[@class="desc"][2]/span/text()'):
            swapped_times = re.sub(r"(.+)\((.+)\)", r"\2 \1", times.get())
            item["opening_hours"].add_ranges_from_string(swapped_times)
        yield item
