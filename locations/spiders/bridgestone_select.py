from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class BridgestoneSelectSpider(SitemapSpider, StructuredDataSpider):
    name = "bridgestone_select"
    item_attributes = {"brand": "Bridgestone", "brand_wikidata": "Q179433"}
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
        apply_category(Categories.SHOP_TYRES, item)
        apply_yes_no("repair", item, True)
        yield item
