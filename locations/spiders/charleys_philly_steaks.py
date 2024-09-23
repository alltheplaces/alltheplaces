import html

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CharleysPhillySteaksSpider(SitemapSpider, StructuredDataSpider):
    name = "charleys_philly_steaks"
    item_attributes = {"brand": "Charley's Philly Steaks", "brand_wikidata": "Q1066777"}
    sitemap_urls = ["https://www.charleys.com/robots.txt"]
    sitemap_follow = ["locations"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse")]
    wanted_types = ["Restaurant"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = html.unescape(item.pop("name"))
        item["website"] = response.url.split("?", 1)[0]

        yield item
