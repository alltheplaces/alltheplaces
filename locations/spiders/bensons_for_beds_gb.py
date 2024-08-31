from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BensonsForBedsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bensons_for_beds_gb"
    item_attributes = {"brand": "Bensons for Beds", "brand_wikidata": "Q4890299"}
    sitemap_urls = ["https://stores.bensonsforbeds.co.uk/robots.txt"]
    sitemap_rules = [(r"uk/[^/]+/[^/]+$", "parse")]
    wanted_types = ["FurnitureStore"]
    search_for_email = False
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Bensons for Beds ")
        yield item
