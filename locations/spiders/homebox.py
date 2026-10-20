from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HomeboxSpider(SitemapSpider, StructuredDataSpider):
    name = "homebox"
    item_attributes = {"brand": "Homebox", "brand_wikidata": "Q127598596", "name": "Homebox"}
    sitemap_urls = ["https://www.homebox.fr/sitemap.xml"]
    sitemap_rules = [(r"/liste-des-gardes-meubles/", "parse_sd")]
    drop_attributes = {"facebook", "image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"].removeprefix("https://www.homebox.fr/liste-des-gardes-meubles/")
        item["branch"] = item.pop("name").removeprefix("HOMEBOX ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
