from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ApotekhjartatSESpider(SitemapSpider, StructuredDataSpider):
    name = "apotekhjartat_se"
    item_attributes = {
        "brand": "Apotek Hjärtat",
        "brand_wikidata": "Q10416114",
    }
    sitemap_urls = ["https://www.apotekhjartat.se/robots.txt"]
    sitemap_rules = [
        (r".*/hitta-apotek-hjartat/.*", "parse"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = "Apotek Hjärtat"
        apply_category(Categories.PHARMACY, item)
        yield item
