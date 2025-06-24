from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.structured_data_spider import StructuredDataSpider


class EquityUSSpider(SitemapSpider, StructuredDataSpider):
    name = "equity_us"
    item_attributes = {
        "operator": "Equity Residential",
        "operator_wikidata": "Q187740",
    }
    requires_proxy = True
    sitemap_urls = ["https://www.equityapartments.com/sitemap.xml"]
    sitemap_rules = [
        (r"/[\w-]+/[\w-]+/[\w-]+-apartments$", "parse"),
    ]
    wanted_types = ["ApartmentComplex"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category({"landuse": "residential", "residential": "apartments"}, item)

        yield item
