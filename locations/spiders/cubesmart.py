from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CubeSmartSpider(SitemapSpider, StructuredDataSpider):
    name = "cubesmart"
    item_attributes = {"brand": "CubeSmart", "brand_wikidata": "Q5192200"}
    allowed_domains = ["www.cubesmart.com"]
    sitemap_urls = ["https://www.cubesmart.com/sitemap-facility.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["SelfStorage"]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lon"] = "-" + item["lon"]

        yield item
