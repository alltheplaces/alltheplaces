
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KonaGrillUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kona_grill_us"
    item_attributes = {
        "brand": "Kona Grill",
        "brand_wikidata": "Q6428706",
    }

    drop_attributes = {"name", "image"}
    search_for_facebook = False

    sitemap_urls = ["https://konagrill.com/locations-sitemap.xml"]
    sitemap_rules = [(r"/location/", "parse_sd")]

    # parse sd returns two locations for every restaurant url, one of which is an office location (the same one for every restaurant)
    # excluding items that link to the kona grill home page excludes this office from the results.
    def post_process_item(self, item, response, ld_item):
        if item["website"] != "https://konagrill.com/":
            yield item
