from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.asda_gb import AsdaGBSpider
from locations.spiders.morrisons_gb import MorrisonsGBSpider
from locations.spiders.sainsburys import SainsburysSpider
from locations.spiders.tesco_gb import TescoGBSpider
from locations.spiders.waitrose import WaitroseSpider


class TimpsonGroupGBIESpider(JSONBlobSpider):
    name = "timpson_group_gb_ie"
    allowed_domains = ["www.maxphoto.co.uk"]
    start_urls = ["https://www.maxphoto.co.uk/storefinder/locator/get/_featured_/_/"]
    locations_key = "locations"
    brands = {
        "johnsons": {
            "brand": "Johnsons",
            "brand_wikidata": "Q6268527",
            "category": Categories.SHOP_DRY_CLEANING,
            "website_template": "https://www.johnsoncleaners.com/branch/{}",
        },
        "maxphoto": {
            "brand": "Max Spielmann",
            "brand_wikidata": "Q76221051",
            "category": Categories.SHOP_PHOTO,
            "website_template": "https://www.maxphoto.co.uk/photo-store-locator/{}",
        },
        "snappysnaps": {
            "brand": "Snappy Snaps",
            "brand_wikidata": "Q7547351",
            "category": Categories.SHOP_PHOTO,
            "website_template": "https://www.snappysnaps.co.uk/{}/more-times",
        },
        "timpson": {
            "brand": "Timspon",
            "brand_wikidata": "Q7807658",
            "category": Categories.SHOP_LOCKSMITH,
            "website_template": "https://www.timpson.co.uk/stores/{}",
        },
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["group"] in self.brands.keys():
            item["brand"] = self.brands[feature["group"]]["brand"]
            item["brand_wikidata"] = self.brands[feature["group"]]["brand_wikidata"]
            item["website"] = self.brands[feature["group"]]["website_template"].format(feature["url"])
            apply_category(self.brands[feature["group"]]["category"], item)
        else:
            self.logger.error("Unknown brand: {}".format(feature["group"]))
            return

        if feature.get("supermarket") and feature["supermarket"] != "0":
            match feature["supermarket"]:
                case "asda":
                    item["located_in"] = AsdaGBSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = AsdaGBSpider.item_attributes["brand_wikidata"]
                case "morrisons":
                    item["located_in"] = MorrisonsGBSpider.MORRISONS["brand"]
                    item["located_in_wikidata"] = MorrisonsGBSpider.MORRISONS["brand_wikidata"]
                case "sainsburys":
                    item["located_in"] = SainsburysSpider.SAINSBURYS["brand"]
                    item["located_in_wikidata"] = SainsburysSpider.SAINSBURYS["brand_wikidata"]
                case "tesco":
                    item["located_in"] = TescoGBSpider.TESCO["brand"]
                    item["located_in_wikidata"] = TescoGBSpider.TESCO["brand_wikidata"]
                case "waitrose":
                    item["located_in"] = WaitroseSpider.WAITROSE["brand"]
                    item["located_in_wikidata"] = WaitroseSpider.WAITROSE["brand_wikidata"]
                case _:
                    self.logger.error(
                        "Unknown supermarket within which this feature is located: {}".format(feature["supermarket"])
                    )
                    return

        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines([feature.get("street1"), feature.get("street2")])
        item["email"] = feature.get("misc5")

        item["opening_hours"] = OpeningHours()
        for day_index, day_abbrev in enumerate(DAYS):
            day_hours = feature["opening_{}".format(day_index + 1)].replace(" ", "")
            if day_hours == "Closed":
                item["opening_hours"].set_closed(day_abbrev)
                continue
            item["opening_hours"].add_range(day_abbrev, *day_hours.split("-", 1))

        yield item
