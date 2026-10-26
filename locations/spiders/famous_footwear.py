from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FamousFootwearSpider(SitemapSpider, StructuredDataSpider):
    name = "famous_footwear"
    item_attributes = {"brand": "Famous Footwear", "brand_wikidata": "Q5433457"}
    sitemap_urls = ["https://www.famousfootwear.com/sitemap.xml", "https://www.famousfootwear.ca/sitemap.xml"]
    sitemap_follow = "stores"
    sitemap_rules = [(r"/stores/[a-z]{2}/[-\w]+/[-\w]+/[-\w]+-(\d+)", "parse_sd")]
    wanted_types = ["Store"]
    search_for_facebook = False
    time_format = "%I:%M%p"
    requires_proxy = True

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["lat"] = response.xpath("//@data-store-latitude").get("")
        item["lon"] = response.xpath("//@data-store-longitude").get("")
        item["branch"] = response.xpath("//@data-store-name").get("")

        apply_category(Categories.SHOP_SHOES, item)

        yield item
