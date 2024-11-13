from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AutoNationUSSpider(SitemapSpider, StructuredDataSpider):
    name = "auto_nation_us"
    allowed_domains = ["autonation.com"]
    item_attributes = {"brand": "AutoNation", "brand_wikidata": "Q784804"}
    sitemap_urls = ["https://www.autonation.com/robots.txt"]
    sitemap_rules = [(r"https://www.autonation.com/dealers/[^/]+$", "parse")]
    wanted_types = ["AutoDealer"]
    time_format = "%I:%M %p"
    requires_proxy = "US"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath('//input[@id="storeLatitude"]/@value').get()
        item["lon"] = response.xpath('//input[@id="storeLongitude"]/@value').get()

        yield item
