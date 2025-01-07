from typing import Iterable

from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.asda_gb import AsdaGBSpider
from locations.spiders.bq import BqSpider
from locations.spiders.homebase_gb_ie import HomebaseGBIESpider
from locations.spiders.leyland_sdm_gb import LeylandSdmGBSpider
from locations.spiders.morrisons_gb import MorrisonsGBSpider
from locations.spiders.robert_dyas_gb import RobertDyasGBSpider
from locations.spiders.sainsburys import SainsburysSpider
from locations.spiders.screwfix_gb import ScrewfixGBSpider
from locations.spiders.tesco_gb import TescoGBSpider
from locations.spiders.the_range import TheRangeSpider
from locations.spiders.waitrose import WaitroseSpider
from locations.spiders.wickes_gb import WickesGBSpider


class TimpsonGroupSpider(JSONBlobSpider):
    name = "timpson_group"
    allowed_domains = ["www.maxphoto.co.uk"]
    start_urls = ["https://www.maxphoto.co.uk/storefinder/locator/get/_all_/"]
    locations_key = "locations"
    brands = {
        "arkhive": {
            # Note: concept store brand (one off) and therefore not likely to
            # be present in Wikidata or NSI.
            "brand": "Arkhive",
            "brand_wikidata": None,
            "category": Categories.SHOP_PHOTO,
            "website_template": None,
        },
        "barbershop": {
            # Note: not currently defined as a separate brand in the API and
            # NSI currently names this brand "Timpson".
            "brand": "Timpson",
            "brand_wikidata": "Q7807658",
            "category": Categories.SHOP_HAIRDRESSER,
            "website_tempalte": None,
        },
        "columbine": {
            "brand": "Columbine",
            "brand_wikidata": None,
            "category": Categories.SHOP_DRY_CLEANING,
            "website_template": None,
        },
        "jeeves": {
            "brand": "Jeeves",
            "brand_wikidata": "Q65052203",
            "category": Categories.SHOP_DRY_CLEANING,
            "website_template": None,
        },
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
            "brand": "Timpson",
            "brand_wikidata": "Q7807658",
            "category": Categories.SHOP_LOCKSMITH,
            "website_template": "https://www.timpson.co.uk/stores/{}",
        },
        "watchlab": {
            "brand": "The Watch Lab",
            "brand_wikidata": None,
            "category": Categories.CRAFT_WATCHMAKER,
            "website_template": None,
        },
        "watchworkshop": {
            "brand": "The Watch Workshop",
            "brand_wikidata": None,
            "category": Categories.CRAFT_WATCHMAKER,
            "website_template": None,
        },
    }

    def start_requests(self) -> Iterable[FormRequest]:
        formdata = {"start": "50000"}
        headers = {"X-Requested-With": "XMLHttpRequest"}
        yield FormRequest(url=self.start_urls[0], formdata=formdata, headers=headers, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["group"] in self.brands.keys():
            item["brand"] = self.brands[feature["group"]]["brand"]
            item["brand_wikidata"] = self.brands[feature["group"]]["brand_wikidata"]

            if self.brands[feature["group"]]["website_template"]:
                item["website"] = self.brands[feature["group"]]["website_template"].format(feature["url"])
            else:
                item.pop("website", None)

            if feature["loc_type"] == "2":
                # Self-service photo printing machine.
                apply_category(Categories.PRINTER, item)
            elif feature["loc_type"] == "4":
                # Photo booth machine.
                apply_category(Categories.PHOTO_BOOTH, item)
            elif feature["loc_type"] == "6":
                # Self-service key cutting machine.
                apply_category(Categories.VENDING_MACHINE_KEYS, item)
            elif feature["loc_type"] == "8":
                # "Barbershop" branded hairdresser.
                apply_category(self.brands["barbershop"]["category"], item)
            else:
                # Includes loc_type of 3 which is a drop-off/pick-up point for
                # dry cleaning.
                apply_category(self.brands[feature["group"]]["category"], item)
        else:
            self.logger.error("Unknown brand: {}".format(feature["group"]))
            return

        if feature.get("supermarket") and feature["supermarket"] != "0":
            self.add_located_in(item, feature["supermarket"])

        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines([feature.get("street1"), feature.get("street2")])
        item["email"] = feature.get("misc5")

        if feature.get("opening_1"):
            if feature["opening_1"].upper() == "TEMPORARILY CLOSED":
                # Store/feature is not open for business and should be ignored.
                return
            item["opening_hours"] = OpeningHours()
            for day_index, day_abbrev in enumerate(DAYS):
                day_hours = feature["opening_{}".format(day_index + 1)].replace(" ", "").replace(".", ":")
                if day_hours.upper() == "CLOSED":
                    item["opening_hours"].set_closed(day_abbrev)
                    continue
                item["opening_hours"].add_range(day_abbrev, *day_hours.split("-", 1))

        yield item

    def add_located_in(self, item: Feature, located_in_brand_key: str) -> None:
        match located_in_brand_key:
            case "asda":
                item["located_in"] = AsdaGBSpider.item_attributes["brand"]
                item["located_in_wikidata"] = AsdaGBSpider.item_attributes["brand_wikidata"]
            case "bq":
                item["located_in"] = BqSpider.item_attributes["brand"]
                item["located_in_wikidata"] = BqSpider.item_attributes["brand_wikidata"]
            case "clothing-care":
                # TODO: unknown brand/feature type.
                pass
            case "homebase":
                item["located_in"] = HomebaseGBIESpider.item_attributes["brand"]
                item["located_in_wikidata"] = HomebaseGBIESpider.item_attributes["brand_wikidata"]
            case "leyland":
                item["located_in"] = LeylandSdmGBSpider.item_attributes["brand"]
                item["located_in_wikidata"] = LeylandSdmGBSpider.item_attributes["brand_wikidata"]
            case "morrisons" | "Morrisons":
                item["located_in"] = MorrisonsGBSpider.MORRISONS["brand"]
                item["located_in_wikidata"] = MorrisonsGBSpider.MORRISONS["brand_wikidata"]
            case "road-chef":
                # TODO: change in the future if ATP implements a Roadchef spider.
                item["located_in"] = "Roadchef"
                item["located_in_wikidata"]: "Q7339582"
            case "robert-dyas":
                item["located_in"] = RobertDyasGBSpider.item_attributes["brand"]
                item["located_in_wikidata"] = RobertDyasGBSpider.item_attributes["brand_wikidata"]
            case "sainsburys":
                item["located_in"] = SainsburysSpider.SAINSBURYS["brand"]
                item["located_in_wikidata"] = SainsburysSpider.SAINSBURYS["brand_wikidata"]
            case "screwfix":
                item["located_in"] = ScrewfixGBSpider.item_attributes["brand"]
                item["located_in_wikidata"] = ScrewfixGBSpider.item_attributes["brand_wikidata"]
            case "sewquick":
                # Single store (not part of a chain) can be ignored.
                pass
            case "tesco":
                item["located_in"] = TescoGBSpider.TESCO["brand"]
                item["located_in_wikidata"] = TescoGBSpider.TESCO["brand_wikidata"]
            case "tfl":
                # Ignore Transport for London as "located_in" is not
                # typically used for branded transport stops.
                pass
            case "the-range":
                item["located_in"] = TheRangeSpider.item_attributes["brand"]
                item["located_in_wikidata"] = TheRangeSpider.item_attributes["brand_wikidata"]
            case "waitrose":
                item["located_in"] = WaitroseSpider.WAITROSE["brand"]
                item["located_in_wikidata"] = WaitroseSpider.WAITROSE["brand_wikidata"]
            case "westfield":
                # Ignore Westfield as "located_in" is not typically used
                # for branded shopping malls.
                pass
            case "wickes":
                item["located_in"] = WickesGBSpider.item_attributes["brand"]
                item["located_in_wikidata"] = WickesGBSpider.item_attributes["brand_wikidata"]
            case _:
                self.logger.error(
                    "Unknown supermarket within which this feature is located: {}".format(located_in_brand_key)
                )
                return
