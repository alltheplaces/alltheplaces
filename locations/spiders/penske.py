import html
import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PenskeSpider(SitemapSpider, StructuredDataSpider):
    name = "penske"
    item_attributes = {"brand_wikidata": "Q81234570"}
    allowed_domains = ["pensketruckrental.com"]
    sitemap_urls = ["https://www.pensketruckrental.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/us/[-\w]+/[-\w]+/[0-9]+/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data):
        item["ref"] = re.findall("[0-9]+", response.url)[0]
        item.pop("email", None)
        item["branch"] = html.unescape(item.pop("name"))

        yield item
