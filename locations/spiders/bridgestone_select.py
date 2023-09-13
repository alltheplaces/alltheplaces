from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BridgestoneSelectSpider(SitemapSpider, StructuredDataSpider):
    name = "bridgestone_select"
    item_attributes = {"brand": "Bridgestone Select Tyre & Auto", "brand_wikidata": "Q122420123"}
    allowed_domains = ["www.bridgestone.com.au", "www.bridgestone.co.nz"]
    sitemap_urls = ["https://www.bridgestone.com.au/sitemap.xml", "https://www.bridgestone.co.nz/sitemap.xml"]
    sitemap_rules = [
        (r"www\.bridgestone\.com\.au\/stores\/(?:act|nsw|nt|qld|sa|tas|vic|wa)\/[\w\-]+$", "parse_sd"),
        (r"www\.bridgestone\.co\.nz\/stores\/[\w\-]+\/[\w\-]+$", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data):
        if ".com.au" in response.url:
            item["country"] = "AU"
        elif ".co.nz" in response.url:
            item.pop("state", None)
            item["country"] = "NZ"
        item.pop("facebook", None)
        if "generic-" in item.get("image", ""):
            item.pop("image", None)
        yield item
