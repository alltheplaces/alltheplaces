# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider


class SuperdrugGBSpider(SitemapSpider, StructuredDataSpider):
    name = "superdrug_gb"
    item_attributes = {"brand": "Superdrug", "brand_wikidata": "Q7643261"}
    sitemap_urls = ["https://www.superdrug.com/sitemap.xml"]
    sitemap_follow = ["Store"]
    sitemap_rules = [(r"https:\/\/www\.superdrug\.com\/store\/(.+)$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    download_delay = 0.5

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }

    def inspect_item(self, item, response):
        item["addr_full"] = clean_address(
            item["street_address"].replace("Superdrug", "")
        )
        item["street_address"] = clean_address(
            item["addr_full"].replace(item["city"], "").replace(item["postcode"], "")
        )
        extract_google_position(item, response)

        # Supplied url has whitespace padding
        item["website"] = response.url

        yield item
