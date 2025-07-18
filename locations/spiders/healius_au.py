from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class HealiusAUSpider(JSONBlobSpider):
    name = "healius_au"
    brands = {
        "ABBOTT": {
            "brand": "Abbott Pathology",
            "brand_wikidata": "Q126165721",
            "category": Categories.SAMPLE_COLLECTION,
            "website": "https://www.abbottpathology.com.au",
        },
        "DOREVITCH": {
            "brand": "Dorevitch Pathology",
            "brand_wikidata": "Q126165490",
            "category": Categories.SAMPLE_COLLECTION,
            "website": "https://www.dorevitch.com.au",
        },
        "LAVERTY": {
            "brand": "Laverty Pathology",
            "brand_wikidata": "Q105256033",
            "category": Categories.SAMPLE_COLLECTION,
            "website": "https://www.laverty.com.au",
        },
        "LUMUS": {
            "brand": "Lumus Imaging",
            "brand_wikidata": "Q130311754",
            # Note: Proposed OSM tag per https://wiki.openstreetmap.org/wiki/Proposal:Medical_Imaging
            "category": Categories.MEDICAL_IMAGING,
            "website": "https://www.lumusimaging.com.au",
        },
        "QML": {
            "brand": "QML Pathology",
            "brand_wikidata": "Q126165557",
            "category": Categories.SAMPLE_COLLECTION,
            "website": "https://www.qml.com.au",
        },
        "TML": {
            "brand": "TML Pathology",
            "brand_wikidata": "Q126165745",
            "category": Categories.SAMPLE_COLLECTION,
            "website": "https://www.tmlpath.com.au",
        },
        "WDP": {
            "brand": "Western Diagnostic Pathology",
            "brand_wikidata": "Q126165699",
            "category": Categories.SAMPLE_COLLECTION,
            "website": "https://www.wdp.com.au",
        },
    }
    allowed_domains = ["api.apps.healius.com.au"]
    start_urls = [
        "https://api.apps.healius.com.au/entity/location/map/location/filtered?fields=ID,ADDRESS,ADDRESS2,BROCHURE,CC_ID,CLOSURES,DAYS,EMAIL,FACILITIES,FAX,GALLERY_IMAGES,HERO_IMAGE,IS_ADF_SITE,LOGO,MODALITIES,NAME,NEXT_OPEN,OPEN_DAYS,OPEN_EARLY_DAYS,OPEN_LATE_DAYS,PHONE,POSITION,SERVICE_TYPE,SPECIAL_TESTS,STATE,STATUS,TODAY_SHIFTS,NOTICE_EXTERNAL,URL&serviceType=ALL"
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        if brand_code := feature.get("logo"):
            brand_code = brand_code.upper()
            if brand_code in self.brands.keys():
                item["name"] = item["brand"] = self.brands[brand_code]["brand"]
                item["brand_wikidata"] = self.brands[brand_code]["brand_wikidata"]
                item["website"] = urljoin(self.brands[brand_code]["website"], f'/locations/{feature["url"]}')
                apply_category(self.brands[brand_code]["category"], item)
            else:
                raise ValueError("Unknown brand code: {}".format(brand_code))

        item["street_address"] = item["addr_full"]
        item["addr_full"] = clean_address([feature.get("address"), feature.get("address2")])
        item["opening_hours"] = self.parse_opening_hours(feature)

        facilities = [facility["icon"] for facility in feature.get("facilities", [])]
        apply_yes_no(Extras.TOILETS, item, "toilet" in facilities, False)
        apply_yes_no(Extras.WHEELCHAIR, item, "wheelChair" in facilities, False)

        yield item

    def parse_opening_hours(self, feature: dict) -> OpeningHours:
        oh = OpeningHours()
        hours_string = ""
        for day_hours in feature.get("days", []):
            if day_hours.get("temporaryChange"):
                continue
            day_abbrev = day_hours["day"].split(" ", 1)[0]
            if day_abbrev in hours_string:
                # Already captured this weekday so the second instance can be
                # ignored. Source data just gives the next two weeks of
                # opening hours by specific day of the year.
                continue
            for shift in day_hours["shifts"]:
                open_time = shift["open"]
                close_time = shift["close"]
                hours_string = f"{hours_string} {day_abbrev}: {open_time} - {close_time}"
        oh.add_ranges_from_string(hours_string)
        return oh
