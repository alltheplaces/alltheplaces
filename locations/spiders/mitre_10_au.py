from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class Mitre10AUSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "mitre_10_au"
    item_attributes = {"brand": "Mitre 10", "brand_wikidata": "Q6882393"}
    allowed_domains = ["mitre10.com.au"]
    sitemap_urls = ["https://www.mitre10.com.au/media/sitemap_retailer_mitre10.xml"]
    sitemap_rules = [
        (r"/stores/.+?-(\d+)$", "parse_sd"),
    ]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item.pop("facebook")
        item.pop("image")
        item["branch"] = item.pop("name").removesuffix("Mitre 10")
        item["addr_full"] = response.xpath('//*[@class="address"]').xpath("normalize-space()").get()
        item["website"] = response.url
        yield item
