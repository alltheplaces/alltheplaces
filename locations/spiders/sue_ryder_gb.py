from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SueRyderGBSpider(SitemapSpider, StructuredDataSpider):
    name = "sue_ryder_gb"
    item_attributes = {"brand": "Sue Ryder", "brand_wikidata": "Q7634271"}
    sitemap_urls = ["https://www.sueryder.org/sitemap.xml"]
    sitemap_rules = [(r"/find-a-shop/([^/]+)/$", "parse_sd")]
    time_format = "%H:%M:%S"
    search_for_image = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")

        yield item
