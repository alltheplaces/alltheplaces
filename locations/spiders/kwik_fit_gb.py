from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KwikFitGBSpider(SitemapSpider, StructuredDataSpider):
    name = "kwik_fit_gb"
    item_attributes = {"brand": "Kwik Fit", "brand_wikidata": "Q958053"}
    sitemap_urls = ["https://www.kwik-fit.com/sitemap.xml"]
    sitemap_rules = [("/locate-a-centre/", "parse_sd")]
    wanted_types = ["AutomotiveBusiness"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Kwik Fit - ")

        extract_google_position(item, response)
        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item

    def extract_amenity_features(self, item: Feature | dict, selector: Selector, ld_item: dict) -> None:
        features = [feat["name"] if feat["value"] == "True" else None for feat in ld_item.get("amenityFeature")]
        apply_yes_no(Extras.TOILETS, item, "Customer Toilets" in features)
        apply_yes_no(Extras.WIFI, item, "Free WiFi" in features)
