from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MilestonesCASpider(SitemapSpider, StructuredDataSpider):
    name = "milestones_ca"
    item_attributes = {"brand": "Milestones", "brand_wikidata": "Q6851623"}
    allowed_domains = ["milestonesrestaurants.com"]
    sitemap_urls = ["https://milestonesrestaurants.com/locations-sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data):
        if ld_data.get("@id") == "https://milestonesrestaurants.com/#organization":
            return
        item.pop("twitter", None)
        item.pop("facebook", None)
        yield item
