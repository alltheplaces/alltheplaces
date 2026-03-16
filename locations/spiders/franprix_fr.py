from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FranprixFRSpider(SitemapSpider, StructuredDataSpider):
    name = "franprix_fr"
    item_attributes = {"brand": "Franprix", "brand_wikidata": "Q2420096"}
    sitemap_urls = ["https://www.franprix.fr/sitemap.xml"]
    sitemap_rules = [(r"/magasins/\d+$", "parse_sd")]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.split("/")[-1]
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
