import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MainEventSpider(SitemapSpider, StructuredDataSpider):
    name = "main_event"
    item_attributes = {"brand": "Main Event", "brand_wikidata": "Q56062981"}
    download_delay = 0.2
    sitemap_urls = ["https://www.mainevent.com/sitemap.xml"]
    sitemap_rules = [(r"\/locations\/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"]
        latitude = re.search(r'\\"latitude\\":(-?\d+\.\d+)', response.text).group(1)
        longitude = re.search(r'\\"longitude\\":(-?\d+\.\d+)', response.text).group(1)
        item["lat"] = float(latitude)
        item["lon"] = float(longitude)

        yield item
