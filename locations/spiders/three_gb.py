from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ThreeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "three_gb"
    item_attributes = {"brand": "Three", "brand_wikidata": "Q407009"}
    sitemap_urls = ["https://locator.three.co.uk/robots.txt"]
    sitemap_rules = [
        (
            r"^https:\/\/locator\.three\.co\.uk\/(london|london-&-ni|midlands|north|south)\/([-a-z]+)\/([-0-9a-z']+)$",
            "parse_sd",
        )
    ]
    wanted_types = ["MobilePhoneStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = item["image"] = None
        item["branch"] = response.xpath('//span[@id="location-name"]/text()').get(default="").removeprefix("Three ")
        item.pop("facebook", None)  # Brand specific not location specific.
        item.pop("twitter", None)  # Brand specific not location specific.
        yield item
