from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class WhsmithSpider(SitemapSpider):
    name = "whsmith"
    item_attributes = {"brand": "WHSmith", "brand_wikidata": "Q1548712"}
    allowed_domains = ["whsmith.co.uk"]
    sitemap_urls = ["https://www.whsmith.co.uk/SiteMap/sitemap-pages.xml"]
    sitemap_rules = [(r"/stores/[-\w]+", "parse")]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = clean_address(response.xpath('//*[@class="shop-styling__address"]/p/text()').getall())
        apply_category(Categories.SHOP_NEWSAGENT, item)
        yield item
