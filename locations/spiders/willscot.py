from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class WillscotSpider(SitemapSpider, StructuredDataSpider):
    name = "willscot"
    item_attributes = {"brand": "WillScot", "brand_wikidata": "Q123415387"}
    sitemap_urls = ["https://www.willscot.com/sitemaps/sitemap-willscot%20us-en.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)

        if item["name"].startswith("Mobile Office Trailers") or item["name"].startswith("Portable Storage Units"):
            item["name"] = None

        yield item
