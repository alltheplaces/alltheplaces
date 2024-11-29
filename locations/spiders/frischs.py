from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FrischsSpider(SitemapSpider, StructuredDataSpider):
    name = "frischs"
    item_attributes = {
        "brand": "Frisch's Big Boy",
        "brand_wikidata": "Q5504660",
    }
    allowed_domains = ["locations.frischs.com"]
    sitemap_urls = [
        "https://locations.frischs.com/robots.txt",
    ]
    sitemap_rules = [
        (r"/\d+/$", "parse_sd"),
    ]
    json_parser = "chompjs"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        name = item.pop("name").split(" ", 1)  # remove store id from branch name
        item["branch"] = name[1] if len(name) > 1 else name
        yield item
