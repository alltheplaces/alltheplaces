from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DickeysBarbecuePitSpider(SitemapSpider, StructuredDataSpider):
    name = "dickeys_barbecue_pit"
    item_attributes = {"brand": "Dickey's Barbecue Pit", "brand_wikidata": "Q19880747"}
    allowed_domains = ["dickeys.com"]
    sitemap_urls = ["https://www.dickeys.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[-\w]+/[-\w]+", "parse_sd")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data):
        item["website"] = response.urljoin(item["website"])
        yield item