from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FoussierFRSpider(SitemapSpider, StructuredDataSpider):
    name = "foussier_fr"
    item_attributes = {"brand": "Foussier", "brand_wikidata": "Q135189843"}
    sitemap_urls = ["https://www.foussier.fr/sitemap-magasins.xml"]
    sitemap_rules = [("/nos-magasins-et-points-de-retrait/", "parse_sd")]
    wanted_items = ["LocalBusiness"]
