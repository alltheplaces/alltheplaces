from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MrBricolageFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mr_bricolage_fr"
    item_attributes = {"brand": "Mr.Bricolage", "brand_wikidata": "Q3141657"}
    sitemap_urls = ["https://magasin.mr-bricolage.fr/locationsitemap1.xml"]
    sitemap_rules = [(r"fr/(\d+)-mr-bricolage-.+$", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Mr.Bricolage ")
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
