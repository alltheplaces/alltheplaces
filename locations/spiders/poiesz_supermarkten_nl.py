from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PoieszSupermarktenNLSpider(SitemapSpider, StructuredDataSpider):
    name = "poiesz_supermarkten_nl"
    item_attributes = {"brand": "Poiesz Supermarkten", "brand_wikidata": "Q2521700"}
    sitemap_urls = ["https://www.poiesz-supermarkten.nl/sitemap.xml"]
    sitemap_rules = [(r"https://www.poiesz-supermarkten.nl/onze-winkels/.*$", "parse_sd")]
 