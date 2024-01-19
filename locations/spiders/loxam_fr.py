from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LoxamFrSpider(SitemapSpider, StructuredDataSpider):
    name = "loxam_fr"
    item_attributes = {"brand": "Loxam", "brand_wikidata": "Q3264407"}
    allowed_domains = ["agence.loxam.fr"]
    sitemap_urls = [
        "https://agence.loxam.fr/locationsitemap1.xml",
        "https://agence.loxam.fr/locationsitemap2.xml",
        "https://agence.loxam.fr/locationsitemap3.xml",
    ]
    sitemap_rules = [("", "parse_sd")]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image", None)
        yield item
