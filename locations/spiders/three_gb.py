from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ThreeGB(SitemapSpider, StructuredDataSpider):
    name = "three_gb"
    item_attributes = {
        "brand": "Three",
        "brand_wikidata": "Q407009",
        "country": "GB",
    }
    sitemap_urls = ["https://locator.three.co.uk/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/locator\.three\.co\.uk\/(london|london-&-ni|midlands|north|south)\/([-a-z]+)\/([-0-9a-z']+)$", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if " closed " in item["name"].lower():
            # Some closed stores still have pages
            return
        yield item
