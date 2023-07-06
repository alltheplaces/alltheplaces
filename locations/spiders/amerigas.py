from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class AmerigasSpider(SitemapSpider):
    name = "amerigas"
    item_attributes = {
        "brand": "AmeriGas",
        "brand_wikidata": "Q23130318",
    }

    # Note, /api/search is forbidden by robots.txt, this spider produces their
    # first-party retail locations only, not third party tank exchange or refill

    sitemap_urls = ["https://www.amerigas.com/local_office_sitemap.xml.gz"]
    sitemap_rules = [
        (r"/locations/propane-offices/[^/]+/[^/]+/[^/]+$", "parse"),
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "LocalBusiness")
        if "extras" not in item:
            item["extras"] = {}
        item["extras"].update({"shop": "gas"})
        yield item
