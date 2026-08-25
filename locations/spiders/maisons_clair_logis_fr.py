from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category


class MaisonsClairLogisFRSpider(SitemapSpider, StructuredDataSpider):
    name = "maisons_clair_logis_fr"
    item_attributes = {
        "brand": "Maisons Clair Logis",
        "brand_wikidata": "Q141175303",
    }
    sitemap_urls = ["https://www.maisonsclairlogis.fr/agence-sitemap.xml"]
    sitemap_rules = [
        (r"", "parse_sd"),
    ]
    drop_attributes = ["facebook", "image"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.CRAFT_BUILDER, item)
        item["branch"] = item.pop("name", "").removeprefix("Maisons Clair Logis ")
        yield item
