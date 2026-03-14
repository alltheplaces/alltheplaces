from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MaisonDeLaLiterieFRSpider(SitemapSpider, StructuredDataSpider):
    name = "maison_de_la_literie_fr"
    item_attributes = {"brand": "Maison de la Literie", "brand_wikidata": "Q80955776"}
    sitemap_urls = ["https://magasins.maisondelaliterie.fr/sitemap_pois.xml"]
    sitemap_rules = [(r".+/details$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Maison de la Literie - ")

        apply_category(Categories.SHOP_BED, item)

        yield item
