from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class Bubbas33USSpider(SitemapSpider, StructuredDataSpider):
    name = "bubbas33_us"
    item_attributes = {"brand": "Bubba's 33", "brand_wikidata": "Q119359352"}
    sitemap_urls = ["https://www.bubbas33.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        extract_google_position(item, response)
        yield item
