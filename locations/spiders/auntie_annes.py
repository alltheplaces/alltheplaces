from scrapy import Selector
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AuntieAnnesSpider(SitemapSpider, StructuredDataSpider):
    name = "auntie_annes"
    item_attributes = {"brand": "Auntie Anne's", "brand_wikidata": "Q4822010"}
    allowed_domains = ["auntieannes.com"]
    sitemap_urls = ["https://locations.auntieannes.com/robots.txt"]
    sitemap_rules = [(r"https://locations\.auntieannes\.com/\w\w/[-.\w]+/[-–\w]+$", "parse_sd")]
    drop_attributes = {"image"}

    def extract_amenity_features(self, item: Feature | dict, selector: Selector, ld_item: dict) -> None:
        if features := ld_item.get("amenityFeature"):
            if isinstance(features, str):
                features = [features]
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in features)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in features)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["branch"] = (
            response.xpath('//meta[@property="og:title"]/@content')
            .get()
            .split(" | ")[0]
            .replace("Auntie Anne's", "")
            .strip(" /")
            .replace(
                "Dallas Ft. Worth Int'lDallas Ft. Worth Int'l Airport (TA;G39) Airport",
                "Dallas Ft. Worth Int'l Airport (TA;G39)",
            )
            .replace(";", ":")
        )
        apply_category(Categories.FAST_FOOD, item)
        yield item
