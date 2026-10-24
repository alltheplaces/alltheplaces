from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SherpaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "sherpa_fr"
    item_attributes = {"brand": "Sherpa", "brand_wikidata": "Q3481967"}
    sitemap_urls = ["https://www.sherpa.net/sitemap.xml"]
    sitemap_rules = [(r"https://www.sherpa.net/magasins/.*\d$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/sherpa.supermarche":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("Sherpa d'").removeprefix("Sherpa de")

        apply_category(Categories.CONVENIENCE, item)
        yield item
