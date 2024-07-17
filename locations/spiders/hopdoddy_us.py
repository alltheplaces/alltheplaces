from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class HopdoddyUSSpider(SitemapSpider, StructuredDataSpider):
    name = "hopdoddy_us"
    item_attributes = {"brand_wikidata": "Q123689179"}
    sitemap_urls = ["https://www.hopdoddy.com/robots.txt"]
    sitemap_rules = [("/locations/", "parse")]
    wanted_types = ["FoodEstablishment"]
    time_format = "%I %p"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = None
        item["opening_hours"] = None  # data is a lie
        item["ref"] = item["website"] = response.url

        extract_google_position(item, response)

        yield item
