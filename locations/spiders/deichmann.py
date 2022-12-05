from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DeichmannSpider(SitemapSpider, StructuredDataSpider):
    name = "deichmann"
    DEICHMANN = {"brand": "Deichmann", "brand_wikidata": "Q664543"}
    DOSENBACH = {"brand": "Dosenbach", "brand_wikidata": "Q2677329"}
    item_attributes = DEICHMANN
    sitemap_urls = [
        "https://stores.deichmann.com/sitemap.xml",
        "https://stores.dosenbach.ch/sitemap.xml",
    ]
    sitemap_rules = [
        (
            r"https://stores\.dosenbach\.ch/[-\w]+/[-\w]+/[-\w]+\.html",
            "parse_sd",
        ),  # CH
        (
            r"https://stores\.deichmann\.com/[-\w]+/[-\w]+/[-\w]+\.html",
            "parse_sd",
        ),  # DE
        (
            r"https://stores\.deichmann\.com/\w\w-\w\w/[-\w]+/[-\w]+/[-\w]+\.html",
            "parse_sd",
        ),  # All the others
    ]
    wanted_types = ["ShoeStore"]

    def sitemap_filter(self, entries):
        for entry in entries:
            # Filter out excessive matches
            if not entry["loc"].endswith("index.html"):
                yield entry

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "dosenbach.ch" in response.url:
            item.update(self.DOSENBACH)

        yield item
