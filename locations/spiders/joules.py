import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JoulesSpider(SitemapSpider, StructuredDataSpider):
    name = "joules"
    item_attributes = {"brand": "Joules", "brand_wikidata": "Q25351738"}
    sitemap_urls = ["https://www.joules.com/sitemap-index.xml"]
    sitemap_follow = ["Joules-GB-EN-Store"]
    sitemap_rules = [("/storelocator/", "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["url"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        coordinates = re.findall(r"(-?\d+\.\d+)", re.search(r"var directionsUrl = (.+);", response.text).group(1))
        item["lat"] = coordinates[0]
        item["lon"] = coordinates[1]

        yield item
