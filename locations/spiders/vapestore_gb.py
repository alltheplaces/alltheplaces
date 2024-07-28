import re

from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import extract_email


class VapestoreGBSpider(SitemapSpider):
    name = "vapestore_gb"
    item_attributes = {"brand": "vapestore", "brand_wikidata": "Q116710778"}
    sitemap_urls = ["https://www.vapestore.co.uk/pub/sitemap/vapestore_sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.vapestore\.co\.uk\/vapestore-([-\w]+)", "parse")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"] != "https://www.vapestore.co.uk/vapestore-index":
                yield entry

    def parse(self, response, **kwargs):
        item = Feature()

        item["ref"] = re.match(self.sitemap_rules[0][0], response.url).group(1)
        item["website"] = response.url

        item["name"] = response.xpath('//div[@class="flt_left"]/strong/text()').get()
        item["addr_full"] = merge_address_lines(response.xpath('//div[@class="flt_left"]/text()').getall())

        extract_email(item, response)
        extract_google_position(item, response)

        return item
