import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GreatClipsSpider(SitemapSpider, StructuredDataSpider):
    name = "great_clips"
    item_attributes = {"brand": "Great Clips", "brand_wikidata": "Q5598967"}
    allowed_domains = ["greatclips.com"]
    sitemap_urls = ["https://salons.greatclips.com/robots.txt"]
    sitemap_rules = [(r"/(?:us|ca)/\w\w/[^/]+/[^/]+$", "parse")]
    wanted_types = ["HealthAndBeautyBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(r"\"latitude\":(-?\d+\.\d+),\"longitude\":(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = m.groups()

        item["branch"] = response.xpath("//h1/text()").get()

        yield item
