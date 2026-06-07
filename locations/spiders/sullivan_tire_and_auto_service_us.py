from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SullivanTireAndAutoServiceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "sullivan_tire_and_auto_service_us"
    item_attributes = {"brand": "Sullivan Tire and Auto Service", "brand_wikidata": "Q121422824"}
    sitemap_urls = ["https://www.sullivantire.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False
    drop_attributes = {"name"}

    def post_process_item(self, item, response, ld_data):
        item["ref"] = item["ref"].split("/")[-1]
        yield item
