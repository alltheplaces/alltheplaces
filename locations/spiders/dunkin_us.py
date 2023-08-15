from scrapy.spiders import SitemapSpider

from locations.categories import apply_yes_no, Extras
from locations.structured_data_spider import StructuredDataSpider


class DunkinUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dunkin_us"
    item_attributes = {"brand": "Dunkin'", "brand_wikidata": "Q847743"}
    allowed_domains = ["locations.dunkindonuts.com"]
    sitemap_urls = ["https://locations.dunkindonuts.com/sitemap.xml"]
    sitemap_rules = [(r"locations\.dunkindonuts\.com\/en\/[a-z]{2}\/", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["ref"] = response.url.split("/")[-1]
        item.pop("image", None)
        item.pop("twitter", None)
        item.pop("facebook", None)
        extra_features = filter(None, [feature.get("name") for feature in ld_data.get("makesOffer")])
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in extra_features, False)
        yield item
