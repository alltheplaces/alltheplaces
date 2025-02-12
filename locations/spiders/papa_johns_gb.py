import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PapaJohnsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "papa_johns_gb"
    item_attributes = {"brand": "Papa John's", "brand_wikidata": "Q2759586"}
    sitemap_urls = ["https://www.papajohns.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.papajohns\.co\.uk\/stores\/([-.\w]+)$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    requires_proxy = True
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = None
        item["website"] = response.url
        item["branch"] = response.xpath("//h1/text()").get().removeprefix("PAPA JOHNS ")
        if m := re.search(r"\((-?\d+\.\d+),(-?\d+\.\d+)\)", response.xpath('.//*[@class="map col"]/img/@src').get()):
            item["lon"], item["lat"] = m.groups()
        yield item
