import json

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SproutsFarmersMarket(SitemapSpider, StructuredDataSpider):
    name = "sprouts_farmer_market"
    allowed_domains = ["www.sprouts.com"]
    item_attributes = {"brand": "Sprouts Farmer Market", "brand_wikidata": "Q7581369"}
    sitemap_urls = ["https://www.sprouts.com/store-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www.sprouts.com\/store\/fl\/*\/*\/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["opening_hours"] = ld_data["openingHours"].replace(",", ";")
        yield item
