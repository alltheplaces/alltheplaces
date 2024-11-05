from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OptikerBodeDESpider(SitemapSpider, StructuredDataSpider):
    name = "optiker_bode_de"
    item_attributes = {"brand": "Optiker Bode", "brand_wikidata": "Q22671892"}
    sitemap_urls = ["https://www.optiker-bode.de/sitemap.xml"]
    sitemap_rules = [(r"/filiale/", "parse_sd")]
    wanted_types = ["Optician"]

    def pre_process_data(self, ld_data: dict, **kwargs):
        """Fix broken JSON-LD"""
        ld_data["address"] = ld_data["address"].strip("PostalAddress ")
        lat, lng = ld_data["geo"].strip("GeoCoordinates ").split(maxsplit=2)
        ld_data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": lat,
            "longitude": lng,
        }
