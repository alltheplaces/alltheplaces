from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JumeirahSpider(SitemapSpider, StructuredDataSpider):
    name = "jumeirah"
    item_attributes = {"brand": "Jumeirah", "brand_wikidata": "Q1331200"}
    sitemap_urls = ["https://www.jumeirah.com/sitemap-en.xml"]
    sitemap_rules = [(r"https://www.jumeirah.com/en/stay/[^/]+/[^/]+$", "parse")]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Maltese Falcon is a yacht.
        if response.url.endswith("/global/maltese-falcon"):
            return
        # The source uses Mallorca's longitude for Lake Como, placing it in France.
        if response.url.endswith("/italy/jumeirah-lake-como"):
            item["lat"] = item["lon"] = None
            item["country"] = "IT"
        item["branch"] = item.pop("name").replace("Jumeirah ", "")
        if address := response.xpath('//h6[normalize-space()="Address"]/following-sibling::*[1]//text()').get():
            item["addr_full"] = address
        apply_category(Categories.HOTEL, item)
        yield item
