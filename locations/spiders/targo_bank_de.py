from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class TargoBankDESpider(SitemapSpider, StructuredDataSpider):
    name = "targo_bank_de"
    item_attributes = {"brand": "Targobank", "brand_wikidata": "Q1455437"}
    sitemap_urls = ["https://www.targobank.de/de/branch-sitemap.aspx"]
    sitemap_rules = [("", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["postcode"] = ld_data.get("address").get("addressLocality")
        item["city"] = ld_data.get("address").get("postalCode")
        item["branch"] = item.pop("name").replace("TARGOBANK ", "")
        apply_category(Categories.BANK, item)
        yield item
