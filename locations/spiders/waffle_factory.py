from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WaffleFactorySpider(SitemapSpider, StructuredDataSpider):
    name = "waffle_factory"
    item_attributes = {"brand": "Waffle Factory", "brand_wikidata": "Q105426923"}
    sitemap_urls = ["https://restaurants.wafflefactory.com/fr/sitemap.xml"]
    sitemap_rules = [(r"https://restaurants.wafflefactory.com/fr/[^/]+/[^/]+/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None
        item["image"] = None
        if item.get("facebook") in (
            "https://www.facebook.com/wafflefactoryofficiel/",
            "https://www.facebook.com/wafflefactory",
            "https://www.facebook.com/search/pages/",
        ):
            item["facebook"] = None

        item["website"] = item["extras"]["website:fr"] = response.url
        item["extras"]["website:en"] = response.xpath('//link[@rel="alternate"][@hreflang="en"]/@href').get()
        apply_category(Categories.FAST_FOOD, item)

        yield item
