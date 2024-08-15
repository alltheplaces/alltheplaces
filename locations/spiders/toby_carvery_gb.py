from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TobyCarveryGBSpider(SitemapSpider, StructuredDataSpider):
    name = "toby_carvery_gb"
    item_attributes = {"brand": "Toby Carvery", "brand_wikidata": "Q7811777"}
    sitemap_urls = ["https://www.tobycarvery.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.tobycarvery\.co\.uk\/restaurants\/[-\w]+\/[-\w]+$",
            "parse_sd",
        )
    ]
    wanted_types = ["Restaurant"]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "/test/" not in entry["loc"]:
                yield entry
