from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SwissLifeFRSpider(SitemapSpider, StructuredDataSpider):
    name = "swiss_life_fr"
    item_attributes = {"brand": "Swiss Life", "brand_wikidata": "Q667350"}
    sitemap_urls = ["https://agences.swisslife.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"/(\d+)/[^/]+/details$", "parse_sd")]
    wanted_types = ["InsuranceAgency"]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "").removeprefix("Swiss Life ")
        item["image"] = None

        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
