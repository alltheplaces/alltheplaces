from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EbGamesAUSpider(SitemapSpider, StructuredDataSpider):
    name = "eb_games_au"
    item_attributes = {"brand": "EB Games", "brand_wikidata": "Q5322604"}
    sitemap_urls = ["https://www.ebgames.com.au/sitemap-stores.xml"]
    sitemap_rules = [(r"/stores/store/(\d+)-[-\w]+$", "parse_sd")]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["website"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.SHOP_VIDEO_GAMES, item)
        yield item
