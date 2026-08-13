from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

K_CITYMARKET = {"brand": "K-Citymarket", "brand_wikidata": "Q11868561"}
K_MARKET = {"brand": "K-Market", "brand_wikidata": "Q11868562"}
K_SUPERMARKET = {"brand": "K-Supermarket", "brand_wikidata": "Q5408668"}


class KMarketFISpider(SitemapSpider, StructuredDataSpider):
    name = "k_market_fi"
    sitemap_urls = ["https://www.k-ruoka.fi/robots.txt"]
    sitemap_follow = ["stores-"]
    sitemap_rules = [("/kauppa/", "parse")]
    wanted_types = ["GroceryStore"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "/kauppa/k-citymarket-" in response.url:
            item["branch"] = item.pop("name").removeprefix("K-Citymarket ")
            item.update(K_CITYMARKET)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "/kauppa/k-market-" in response.url:
            item["branch"] = item.pop("name").removeprefix("K-Market ")
            item.update(K_MARKET)
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif "/kauppa/k-supermarket-" in response.url:
            item["branch"] = item.pop("name").removeprefix("K-Supermarket ")
            item.update(K_SUPERMARKET)
            apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
