import html

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ProfileNLSpider(SitemapSpider, StructuredDataSpider):
    name = "profile_nl"
    item_attributes = {"brand": "Profile", "brand_wikidata": "Q124339994"}
    sitemap_urls = ["https://www.profiledefietsspecialist.nl/robots.txt"]
    sitemap_rules = [("/fietsenwinkel/", "parse")]
    wanted_types = ["BikeStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = html.unescape(item["name"])
        item["city"] = html.unescape(item["city"])

        yield item
