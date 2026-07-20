from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

FRANPRIX = {"brand": "Franprix", "brand_wikidata": "Q2420096"}
MARCHE = {"brand_wikidata": "Q130165186"}


class FranprixFRSpider(SitemapSpider, StructuredDataSpider):
    name = "franprix_fr"
    sitemap_urls = ["https://www.franprix.fr/sitemap.xml"]
    sitemap_rules = [(r"/magasins/\d+$", "parse_sd")]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"].lower().startswith("franprix "):
            item["name"] = None
            item.update(FRANPRIX)
        elif item["name"].startswith("Marché d'à Côté "):
            item["name"] = None
            item.update(MARCHE)

        item["ref"] = response.url.split("/")[-1]
        item["website"] = response.url

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
