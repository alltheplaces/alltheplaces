import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature


class FreshchoiceNZSpider(CrawlSpider):
    name = "freshchoice_nz"
    item_attributes = {"brand": "FreshChoice", "brand_wikidata": "Q22271877"}
    allowed_domains = ["store.freshchoice.co.nz"]
    start_urls = ["https://store.freshchoice.co.nz/multipage"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//a[contains(@class, "StoreLink--Default")]'), callback="parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Avoid many robots.txt queries as each store is a subdomain

    def parse(self, response):
        properties = {
            "ref": response.url,
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
            "website": response.url,
        }
        hours_string = " ".join(
            response.xpath('//div[@class="Footer__Column"]//dl[@class="TradingHours__Days"]//text()').getall()
        ).replace("day ", "day: ")
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
