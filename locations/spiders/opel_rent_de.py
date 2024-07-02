from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class OpelRentDESpider(SitemapSpider, StructuredDataSpider):
    name = "opel_rent_de"
    item_attributes = {"brand": "Opel Rent", "brand_wikidata": "Q40966"}
    sitemap_urls = ["https://www.opelrent.de/sitemap.xml"]
    sitemap_rules = [(r"/mietwagen-partner/[^/]+-(\d+)/$", "parse")]
    wanted_types = ["AutoRental"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"], item["branch"] = item.pop("name").split(" - ", 1)

        apply_category(Categories.CAR_RENTAL, item)

        yield item
