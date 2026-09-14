from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LaforetImmobilierFRSpider(SitemapSpider, StructuredDataSpider):
    name = "laforet_immobilier_fr"
    item_attributes = {"brand": "Laforêt", "brand_wikidata": "Q56310946"}
    sitemap_urls = ["https://www.laforet.com/storage/sitemaps/agences-immobilieres.xml"]
    sitemap_rules = [("/agence-immobiliere/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
