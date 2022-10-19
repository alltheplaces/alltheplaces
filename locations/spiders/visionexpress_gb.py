# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class VisionExpressGBSpider(SitemapSpider, StructuredDataSpider):
    name = "visionexpress_gb"
    item_attributes = {"brand": "VisionExpress", "brand_wikidata": "Q7936150"}
    sitemap_urls = ["https://www.visionexpress.com/sitemap.xml"]
    sitemap_rules = [("/opticians/", "parse_sd")]
    download_delay = 0.2

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = item["street_address"].replace(" undefined", "")
        # TODO: when there is an agreed solution to this.
        # if "-tesco" in response.url:
        #    set_located_in(item, "Tesco Extra", "Q25172225")
        extract_google_position(item, response)
        yield item
