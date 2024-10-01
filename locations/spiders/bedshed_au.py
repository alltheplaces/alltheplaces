import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BedshedAUSpider(SitemapSpider, StructuredDataSpider):
    name = "bedshed_au"
    item_attributes = {"brand": "Bedshed", "brand_wikidata": "Q84452962"}
    sitemap_urls = ["https://www.bedshed.com.au/sitemap-stores.xml"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(r"latitude&quot;:(-?\d+\.\d+),", response.text):
            item["lat"] = m.group(1)
        if m := re.search(r"longitude&quot;:(-?\d+\.\d+),", response.text):
            item["lon"] = m.group(1)

        yield item
    drop_attributes = {"image"}
