from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, Vending, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CampingCarParkSpider(SitemapSpider, StructuredDataSpider):
    name = "camping_car_park"
    item_attributes = {
        "brand": "Camping-Car Park",
        "brand_wikidata": "Q127751797",
    }
    sitemap_urls = ["https://www.campingcarpark.com/sitemap/en_GB.xml"]
    sitemap_rules = [(r"/motor-home/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = ["image"]
    search_for_amenity_features = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.CARAVAN_SITE, item)

        slug = item.get("website").split("/motor-home/")[1]
        lang = "en_GB/motor-home"
        match item.get("country").lower():
            case "spain":
                lang = "es_ES/estancia-autocaravanas"
            case "france":
                lang = "fr_FR/camping-car"
            case "portugal":
                lang = "pt_PT/estadias-autocaravanas"
            case "germany":
                lang = "de_DE/wohnmobilaufenthalt"

        item["website"] = "https://www.campingcarpark.com/" + lang + "/" + slug
        item["branch"] = item.pop("name", "")
        yield item

    def extract_amenity_features(self, item: Feature, response: Response, ld_item: dict):
        for feature in ld_item.get("amenityFeature") or []:
            match feature.get("name") or "":
                case "Drainage":
                    apply_yes_no(
                        Extras.SANITARY_DUMP_STATION, item, feature.get("value")
                    )  # should be "customers" instead of "yes" ?
                case "Water":
                    apply_yes_no(Extras.DRINKING_WATER, item, feature.get("value"))
                case "Wifi":
                    apply_yes_no(Extras.WIFI, item, feature.get("value"))
                case "Electricity":
                    apply_yes_no(Extras.POWER_SUPPLY, item, feature.get("value"))
                case "Launderette":
                    apply_yes_no(Extras.LAUNDRY, item, feature.get("value"))
                # case _:
                # ignore Security and Selective sorting features
