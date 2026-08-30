from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class HRBlockSpider(SitemapSpider, PlaywrightSpider):
    name = "h_r_block"
    item_attributes = {"brand": "H&R Block", "brand_wikidata": "Q5627799"}
    sitemap_urls = ["https://www.hrblock.com/sitemap.xml"]
    sitemap_rules = [(r"/tax-office-near-me/[^/]+/[^/]+/\d+/?$", "parse_office")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,
        "METAREFRESH_ENABLED": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "ROBOTSTXT_OBEY": False,
    }
    sitemap_follow = ["opp"]

    def parse_office(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.xpath("//@data-office-id").get()
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        item["website"] = response.url
        item["phone"] = response.xpath('//a[contains(@class, "phone-num")]/text()').get()

        address_lines = [
            "".join(span.xpath(".//text()").getall()).strip()
            for span in response.xpath('//div[@class="lbl-address"]/span')
        ]
        address_lines = [line for line in address_lines if line]
        if len(address_lines) >= 4:
            item["postcode"] = address_lines[-1]
            item["state"] = address_lines[-2]
            item["city"] = address_lines[-3].rstrip(",").strip()
            item["country"] = "US"

            item["street_address"] = merge_address_lines(address_lines[:-3])

        apply_category({"office": "tax_advisor"}, item)

        yield item
