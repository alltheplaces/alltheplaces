from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MatmutFRSpider(SitemapSpider, StructuredDataSpider):
    name = "matmut_fr"
    item_attributes = {"brand": "Matmut", "brand_wikidata": "Q3299185"}
    allowed_domains = ["agences.matmut.fr"]
    sitemap_urls = ["https://agences.matmut.fr/sitemap.xml"]
    sitemap_rules = [(r"/matmut-assurances-[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
