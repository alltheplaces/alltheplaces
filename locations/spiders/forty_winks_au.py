from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class FortyWinksAUSpider(SitemapSpider, PlaywrightSpider, StructuredDataSpider):
    name = "forty_winks_au"
    item_attributes = {"brand": "Forty Winks", "brand_wikidata": "Q106283438"}
    allowed_domains = ["www.fortywinks.com.au"]
    sitemap_urls = ["https://www.fortywinks.com.au/sitemap.xml"]
    sitemap_rules = [(r"/store-finder/[^/]+/[^/]+/$", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.strip("/").split("/")[-1]
        item["branch"] = item.pop("name").removeprefix("Forty Winks ")
        item["image"] = None

        apply_category(Categories.SHOP_BED, item)

        yield item
