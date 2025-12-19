from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class GreystarSpider(SitemapSpider, StructuredDataSpider):
    name = "greystar"
    item_attributes = {
        "operator": "Greystar",
        "operator_wikidata": "Q60749135",
    }
    sitemap_urls = ["https://www.greystar.com/sitemap-pdp.xml"]
    sitemap_rules = [
        (r"", "parse"),
    ]
    wanted_types = ["LodgingBusiness"]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = ld_data["latitude"]
        item["lon"] = ld_data["longitude"]
        item["ref"] = ld_data["identifier"]
        if len(ld_data["image"]) > 0:
            item["image"] = ld_data["image"][0]
        apply_category(Categories.RESIDENTIAL_APARTMENTS, item)
        yield item

    def extract_amenity_features(self, item, response, ld_item):
        for amenity_feature in ld_item["amenityFeature"]:
            if amenity_feature["name"] == "Air Conditioning":
                apply_yes_no(Extras.AIR_CONDITIONING, item, amenity_feature["value"], False)
            elif amenity_feature["name"] == "Pet Friendly":
                apply_yes_no(Extras.PETS_ALLOWED, item, amenity_feature["value"], False)
            elif amenity_feature["name"] == "Pool":
                apply_yes_no(Extras.SWIMMING_POOL, item, amenity_feature["value"], False)
            elif amenity_feature["name"] == "Smoke Free":
                apply_yes_no(Extras.SMOKING, item, not amenity_feature["value"], False)
