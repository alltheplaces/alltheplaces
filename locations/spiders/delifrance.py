from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DelifranceSpider(SitemapSpider, StructuredDataSpider):
    name = "delifrance"
    item_attributes = {"brand": "Delifrance", "brand_wikidata": "Q5320229"}
    sitemap_urls = ["https://delifrancerestaurants.com/sitemap.xml"]
    sitemap_rules = [(r"/delifrancerestaurants.com/", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    country_mapping = {
        "Nederland": "NL",
        "België": "BE",
        "India": "IN",
        "Malaysia": "MY",
    }

    def post_process_item(self, item, response, ld_data, **kwargs):
        country_code = self.country_mapping.get(item["country"])
        item["country"] = item["country"] if country_code is None else country_code
        yield item
