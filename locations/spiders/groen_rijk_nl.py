from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GroenRijkNLSpider(SitemapSpider, StructuredDataSpider):
    name = "groen_rijk_nl"
    item_attributes = {"brand": "GroenRijk", "brand_wikidata": "Q2738788"}
    sitemap_urls = ["https://www.groenrijk.nl/robots.txt"]
    sitemap_rules = [("/vestiging/", "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        if geo := ld_data["address"].get("geo"):
            ld_data["geo"] = geo
