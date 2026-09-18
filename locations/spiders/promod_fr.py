from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class PromodFRSpider(SitemapSpider, StructuredDataSpider):
    name = "promod_fr"
    item_attributes = {"brand": "Promod", "brand_wikidata": "Q3407429"}
    sitemap_urls = ["https://www.promod.fr/sitemap-stores/sitemap_geo.xml"]
    sitemap_rules = [(r"/fr-fr/stores/france/.+", "parse_sd")]
    wanted_types = ["ClothingStore"]
    drop_attributes = ["image", "facebook"]

    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            if "/promod-villefranche-s/saone-nationale-372/" in request.url:
                request = request.replace(
                    url=request.url.replace("/promod-villefranche-s/saone", "/promod-villefranche-s-saone")
                )
            yield request

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = (item.pop("name") or "").removeprefix("PROMOD ").lstrip("- ")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
