from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AmerigasSpider(SitemapSpider, StructuredDataSpider):
    name = "amerigas"
    item_attributes = {
        "brand": "AmeriGas",
        "brand_wikidata": "Q23130318",
        "extras": {"amenity": "vending_machine", "vending": "gas"},
    }

    # Note, /api/search is forbidden by robots.txt, this spider produces their
    # first-party retail locations only, not third party tank exchange or refill

    sitemap_urls = ["https://www.amerigas.com/local_office_sitemap.xml.gz"]
    sitemap_rules = [
        (r"/locations/propane-offices/[^/]+/[^/]+/[^/]+$", "parse_sd"),
    ]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["openingHoursSpecification"] = None
