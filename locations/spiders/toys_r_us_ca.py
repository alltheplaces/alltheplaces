from datetime import datetime
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ToysRUSCASpider(SitemapSpider):
    name = "toys_r_us_ca"
    item_attributes = {"brand": "Toys R Us", "brand_wikidata": "Q85847837"}
    sitemap_urls = ["https://www.toysrus.ca/sitemap-stores.xml"]
    sitemap_rules = [(r"^https://www\.toysrus\.ca/storelocator/", "parse_store")]

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        title = response.xpath('//h1[@class="store-title"]/text()').get("").removeprefix("Toy Store in ")
        item["branch"] = title.split(",", 1)[0].strip()

        address_section = response.xpath('//h3[text()="Address"]/following-sibling::p/text()').getall()
        item["addr_full"] = merge_address_lines(address_section)

        item["phone"] = (
            response.xpath('//h3[text()="Phone"]/following-sibling::p//a/@href').get("").removeprefix("tel:")
        )

        oh = OpeningHours()
        for day in DAYS_FULL:
            hours = response.xpath(
                f'//td[@class="day-name" and normalize-space()="{day}"]/following-sibling::td[@class="day-hours"]/text()'
            ).get("")
            open_time, _, close_time = (t.strip() for t in hours.partition("–"))
            try:
                if datetime.strptime(open_time, "%I:%M %p") < datetime.strptime(close_time, "%I:%M %p"):
                    oh.add_range(day, open_time, close_time, time_format="%I:%M %p")
            except ValueError:
                continue
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_TOYS, item)

        yield item
