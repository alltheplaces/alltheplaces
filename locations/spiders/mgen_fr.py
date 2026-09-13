from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MgenFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mgen_fr"
    item_attributes = {"brand": "MGEN", "brand_wikidata": "Q3331039"}
    sitemap_urls = ["https://proximite.mgen.fr/locationsitemap1.xml"]
    sitemap_rules = [(r"https://proximite\.mgen\.fr/.+", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
