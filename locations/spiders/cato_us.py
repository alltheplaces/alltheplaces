from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CatoUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cato_us"
    item_attributes = {"brand": "Cato", "brand_wikidata": "Q16956136"}
    sitemap_urls = ["https://stores.catofashions.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+$", "parse")]
    wanted_types = ["ClothingStore"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Cato Fashions ")
        yield item
