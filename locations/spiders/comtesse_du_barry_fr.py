from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ComtesseDuBarryFRSpider(SitemapSpider, StructuredDataSpider):
    name = "comtesse_du_barry_fr"
    item_attributes = {"brand": "Comtesse du Barry", "brand_wikidata": "Q17176547"}
    sitemap_urls = ["https://boutiques.comtessedubarry.com/locationsitemap1.xml"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image", None)  # Generic brand image, not per-location
        yield item
