from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.mediamarkt import MEDIAMARKT
from locations.structured_data_spider import StructuredDataSpider


class MediamarktTRSpider(SitemapSpider, StructuredDataSpider):
    name = "mediamarkt_tr"
    item_attributes = MEDIAMARKT
    sitemap_urls = ["https://www.mediamarkt.com.tr/sitemaps/sitemap-marketpages.xml"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("MediaMarkt ")
        item["phone"] = None

        apply_category(Categories.SHOP_ELECTRONICS, item)

        yield item
