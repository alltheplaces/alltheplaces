from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class JumboCHSpider(SitemapSpider, StructuredDataSpider):
    name = "jumbo_ch"
    item_attributes = {
        "brand": "Jumbo",
        "brand_wikidata": "Q1713190",
        "country": "CH",
    }
    allowed_domains = ["www.jumbo.ch"]
    sitemap_urls = ["https://www.jumbo.ch/sitemap.xml"]
    sitemap_follow = ["/sitemap/STORE-de-"]
    sitemap_rules = [(r"_POS$", "parse_sd")]
    custom_settings =  DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}
    is_playwright_spider = True
    requires_proxy = True

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["street_address"] = response.xpath('//*[@itemprop="streetAddress"]/text()').get()
        item["addr_full"] = ",".join(response.xpath('//*[@itemprop="address"]//text()').getall())
        item["lat"] = response.xpath('//*[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/@content').get()
        oh = OpeningHours()
        for day_time in (
            response.xpath('//*[@class="vst-detail-openingHours__table"]').xpath("normalize-space()").getall()
        ):
            oh.add_ranges_from_string(day_time, DAYS_DE)
        item["opening_hours"] = oh
        yield item
