from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MacifFRSpider(SitemapSpider, StructuredDataSpider):
    name = "macif_fr"
    item_attributes = {"brand": "Macif", "brand_wikidata": "Q3331021"}
    sitemap_urls = ["https://agences.macif.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"/details$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.OFFICE_INSURANCE, item)
        # Phone number is a shared national hotline, identical across all branches
        item["phone"] = None
        yield item
