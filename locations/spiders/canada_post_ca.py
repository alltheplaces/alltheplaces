from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider

CANADA_POST = {"brand": "Canada Post", "brand_wikidata": "Q1032001"}


class CanadaPostCASpider(ArcGISFeatureServerSpider):
    name = "canada_post_ca"
    host = "pub.geo.canadapost-postescanada.ca"
    context_path = "server"
    service_id = "Hosted/FPO_FLEX_FACILITY_RETAIL_POINT"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["site"]
        item.pop("name", None)
        item["name"] = feature["displaynameen"]
        item["street_address"] = feature["structureaddress"]
        item["opening_hours"] = self.parse_opening_hours(feature)
        item["website"] = item["extras"]["website:en"] = (
            "https://www.canadapost-postescanada.ca/cpc/en/tools/find-a-post-office.page?outletId={}&detail=true".format(
                feature["costcentre"]
            )
        )
        item["extras"]["website:fr"] = (
            "https://www.canadapost-postescanada.ca/scp/fr/outils/trouver-un-bureau-de-poste.page?idComptoir={}&detail=vrai".format(
                feature["costcentre"]
            )
        )

        if feature["grouping"] == "Post Office":
            item.update(CANADA_POST)
            apply_category(Categories.POST_OFFICE, item)
        elif feature["grouping"] == "Pick and Drop":
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["operator"] = feature["sitebusinessname"]
            item["extras"]["post_office:brand"] = CANADA_POST["brand"]
            item["extras"]["post_office:brand:wikidata"] = CANADA_POST["brand_wikidata"]
            item["extras"]["post_office:letter_from"] = "Canada Post"
            item["extras"]["post_office:parcel_from"] = "Canada Post"
            item["extras"]["post_office:parcel_to"] = "Canada Post"
            item["extras"]["post_office:stamps"] = "Canada Post"
            item["extras"]["post_office:packaging"] = "Canada Post"
        elif feature["grouping"] == "Parcel Pickup":
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["operator"] = feature["sitebusinessname"]
            item["extras"]["post_office:brand"] = CANADA_POST["brand"]
            item["extras"]["post_office:brand:wikidata"] = CANADA_POST["brand_wikidata"]
            item["extras"]["post_office:parcel_to"] = "Canada Post"
        elif feature["grouping"] == "Post Point":
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["operator"] = feature["sitebusinessname"]
            item["extras"]["post_office:brand"] = CANADA_POST["brand"]
            item["extras"]["post_office:brand:wikidata"] = CANADA_POST["brand_wikidata"]
        else:
            self.crawler.stats.inc_value(f'{self.name}/unknown_feature_type/{feature["grouping"]}')

        yield item

    def parse_opening_hours(self, feature: dict) -> OpeningHours:
        hours_keys_list = [
            ("Mo", "openmonam", "closemonam", "openmonpm", "closemonpm"),
            ("Tu", "opentueam", "closetueam", "opentuepm", "closetuepm"),
            ("We", "openwedam", "closewedam", "openwedpm", "closewedpm"),
            ("Th", "openthuam", "closethuam", "openthupm", "closethupm"),
            ("Fr", "openfriam", "closefriam", "openfripm", "closefripm"),
            ("Sa", "opensatam", "closesatam", "opensatpm", "closesatpm"),
            ("Su", "opensunam", "closesunam", "opensunpm", "closesunpm"),
        ]
        oh = OpeningHours()
        for hours_keys in hours_keys_list:
            day_abbrev = hours_keys[0]
            am_open = feature.get(hours_keys[1])
            am_close = feature.get(hours_keys[2])
            pm_open = feature.get(hours_keys[3])
            pm_close = feature.get(hours_keys[4])
            if am_open and not am_close and not pm_open and pm_close:
                oh.add_range(day_abbrev, am_open, pm_close, "%H:%M:%S")
            elif am_open and am_close and pm_open and pm_close:
                oh.add_range(day_abbrev, am_open, am_close, "%H:%M:%S")
                oh.add_range(day_abbrev, pm_open, pm_close, "%H:%M:%S")
        return oh
