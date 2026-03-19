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
            item["branch"] = item.pop("name").split(" ", 1)[1]
            item.update(FRANPRIX)
        elif item["name"].startswith("Marché d'à Côté "):
            item["branch"] = item.pop("name").removeprefix("Marché d'à Côté ")
            item.update(MARCHE)

        item["ref"] = response.url.split("/")[-1]
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
