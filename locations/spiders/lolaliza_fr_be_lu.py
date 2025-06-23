from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LolalizaFRBELUSpider(SitemapSpider, StructuredDataSpider):
    name = "lolaliza_fr_be_lu"
    item_attributes = {"brand": "LolaLiza", "brand_wikidata": "Q122840142"}
    sitemap_urls = ["https://stores.lolaliza.com/sitemap.xml"]
    sitemap_rules = [(r"/nl_BE/lolaliza-.*", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("LolaLiza ", "")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
