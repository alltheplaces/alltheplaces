from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class DogHausUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dog_haus_us"
    item_attributes = {
        "brand": "Dog Haus",
        "brand_wikidata": "Q105529843",
    }
    sitemap_urls = ["https://locations.doghaus.com/sitemap.xml"]
    sitemap_rules = [
        (r"^https://locations.doghaus.com/locations/\w\w/[\w-]+/[\w-]+$", "parse"),
    ]
    search_for_facebook = False
    search_for_twitter = False

    def extract_amenity_features(self, item, response, ld_item):
        features = {f["name"] for f in ld_item["amenityFeature"]}
        apply_yes_no(Extras.BAR, item, "Bar Onsite" in features)
        apply_yes_no(Extras.HIGH_CHAIR, item, "High Chairs Available" in features)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "Outdoor Seating" in features)
        apply_yes_no(Extras.TOILETS, item, "Restrooms Available" in features)
        apply_yes_no(Extras.INDOOR_SEATING, item, "Seating Available" in features)
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "Wheelchair Accessible Restroom" in features)
        if "Wheelchair Accessible Entrance" in features and "Wheelchair Accessible Seating" in features:
            apply_yes_no(Extras.WHEELCHAIR, item, True)
        elif "Wheelchair Accessible Entrance" in features or "Wheelchair Accessible Seating" in features:
            apply_yes_no(Extras.WHEELCHAIR_LIMITED, item, True)
