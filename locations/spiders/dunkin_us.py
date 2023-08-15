from chompjs import parse_js_object
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class DunkinUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dunkin_us"
    item_attributes = {"brand": "Dunkin'", "brand_wikidata": "Q847743"}
    allowed_domains = ["locations.dunkindonuts.com"]
    sitemap_urls = ["https://locations.dunkindonuts.com/sitemap.xml"]
    sitemap_rules = [(r"locations\.dunkindonuts\.com\/en\/[a-z]{2}\/[\w\-]+\/[\w\-]+\/\d+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        data_js = parse_js_object(
            response.xpath('//head/script[contains(text(), "__INITIAL__DATA__ = ")]/text()')
            .get()
            .split("__INITIAL__DATA__ = ", 1)[1]
        )
        item["ref"] = data_js["document"]["id"]
        if data_js["document"].get("geocodedCoordinate"):
            # Some location pages do not provide coordinates.
            item["lat"] = data_js["document"]["geocodedCoordinate"]["latitude"]
            item["lon"] = data_js["document"]["geocodedCoordinate"]["longitude"]
        item.pop("facebook", None)
        for social_link in data_js["document"]["ref_listings"]:
            if social_link["publisher"] == "FACEBOOK":
                # Most locations have their own Facebook page which
                # can be used instead of the brand-wide Facebook page.
                item["facebook"] = social_link["listingUrl"]
                break
        item.pop("twitter")
        item.pop("image", None)
        extra_features = filter(None, [feature.get("name") for feature in ld_data.get("makesOffer")])
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in extra_features, False)
        yield item
