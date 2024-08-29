from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SharpsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "sharps_gb"
    item_attributes = {"brand": "Sharps", "brand_wikidata": "Q92453571"}
    sitemap_urls = ["https://www.sharps.co.uk/robots.txt"]
    sitemap_rules = [(r"/find-a-showroom/([^/]+)$", "parse_sd")]
    wanted_types = ["FurnitureStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"], item["lon"] = item["lon"], item["lat"]
        item["branch"] = item.pop("name").removeprefix("Sharps ")

        yield item
