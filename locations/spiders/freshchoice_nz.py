import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class FreshchoiceNZSpider(CrawlSpider):
    name = "freshchoice_nz"
    item_attributes = {"brand": "FreshChoice", "brand_wikidata": "Q22271877"}
    allowed_domains = ["store.freshchoice.co.nz"]
    start_urls = ["https://store.freshchoice.co.nz/multipage"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[contains(@href, ".store.freshchoice.co.nz")]'), callback="parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "CONCURRENT_REQUESTS": 1}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        url = response.url.replace("/catalogues", "")
        properties = {
            "ref": url,
            "name": response.xpath('//meta[@property="og:title"]/@content').get("").strip(),
            "addr_full": re.sub(
                r"\s+",
                " ",
                " ".join(
                    response.xpath(
                        '//div[@class="Footer__Column"]//a[contains(@href, "maps.google.com")]/text()'
                    ).getall()
                ),
            ).strip(),
            "phone": response.xpath('//div[@class="Footer__Column"]//a[contains(@href, "tel:")]/@href')
            .get("")
            .replace("tel:", "")
            .strip(),
            "email": response.xpath('//div[@class="Footer__Column"]//a[contains(@href, "mailto:")]/@href')
            .get("")
            .replace("mailto:", "")
            .strip(),
            "website": url,
        }

        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(
            " ".join(
                response.xpath('//div[@class="Footer__Column"]//dl[@class="TradingHours__Days"]//text()').getall()
            ).replace("day ", "day: ")
        )
        apply_category(Categories.SHOP_SUPERMARKET, properties)
        yield Feature(**properties)
