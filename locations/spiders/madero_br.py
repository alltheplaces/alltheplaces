from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MaderoBRSpider(SitemapSpider, StructuredDataSpider):
    name = "madero_br"
    item_attributes = {"brand": "Madero", "brand_wikidata": "Q115206711"}
    sitemap_urls = ["https://www.restaurantemadero.com.br/pt/sitemap.xml"]
    sitemap_rules = [(r"/restaurante/\w\w/[-\w]+/[-\w]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if name := item.pop("name", None):
            item["branch"] = " ".join(name.split())
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()

        apply_category(Categories.FAST_FOOD, item)

        yield item
