from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PapaJohnsSpider(SitemapSpider, StructuredDataSpider):
    name = "papa_johns"
    item_attributes = {"brand": "Papa John's", "brand_wikidata": "Q2759586"}
    allowed_domains = ["papajohns.com"]
    sitemap_urls = ["https://locations.papajohns.com/sitemap.xml"]
    sitemap_rules = [(r"com/(?:united\-states|canada)/\w{2}/[-\w]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["ref"].strip("/.")
        if item.get("name").startswith("Coming Soon - "):
            item["opening_hours"] = "off"
        item["name"] = item["image"] = None

        item["website"] = response.url

        yield item
