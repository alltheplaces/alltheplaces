from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class EbGamesAUSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "eb_games_au"
    item_attributes = {"brand": "EB Games", "brand_wikidata": "Q5322604"}
    requires_proxy = True
    sitemap_urls = ["https://www.ebgames.com.au/sitemap-stores.xml"]
    sitemap_rules = [(r"/stores/store/(\d+)-[-\w]+$", "parse_sd")]
    search_for_facebook = False
    search_for_twitter = False
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["website"] = response.url
        item["branch"] = item.pop("name")
        extract_google_position(item, response)
        apply_category(Categories.SHOP_VIDEO_GAMES, item)
        yield item
