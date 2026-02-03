from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider

FEATURES_MAPPING = {
    # Fuel types
    "91 premium non-ethanol": Fuel.OCTANE_91,
    "diesel": Fuel.DIESEL,
    "ev tesla": Fuel.ELECTRIC,
    "propane refills": Fuel.PROPANE,
    # Services
    "atm": Extras.ATM,
    "car wash": Extras.CAR_WASH,
    "free air": Extras.COMPRESSED_AIR,
    "restroom": Extras.TOILETS,
}


class StewartsShopsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "stewarts_shops_us"
    item_attributes = {"brand": "Stewart's Shops", "brand_wikidata": "Q7615690"}
    sitemap_urls = ["https://locations.stewartsshops.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z]{2}/[\w-]+/\d+$", "parse_sd")]
    search_for_amenity_features = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.split("/")[-1]
        item["branch"] = (item.pop("name") or "").split("- #", 1)[0]

        # Parse features from HTML checkmarks
        features = response.xpath('//span[preceding-sibling::img[contains(@alt, "Check mark")]]/text()').getall()
        features = [f.strip().lower() for f in features]

        for feature in features:
            if tag := FEATURES_MAPPING.get(feature):
                apply_yes_no(tag, item, True)

        # Check for 24 hours
        if "24 hours" in features:
            item["opening_hours"] = "24/7"

        # Category
        if ld_data.get("@type") == "GasStation" or "gas station" in features:
            fuel = item.deepcopy()
            fuel["ref"] = "{}-FUEL".format(fuel["ref"])
            apply_category(Categories.FUEL_STATION, fuel)
            yield fuel

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
