import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CentralFoodRetailTHSpider(JSONBlobSpider):
    name = "central_food_retail_th"
    allowed_domains = ["corporate.tops.co.th"]
    start_urls = ["https://corporate.tops.co.th:8080/get-all-store?store_format=tops"]
    brands = {
        "Central Food Hall": ("Tops Food Hall", "Q134932513", Categories.SHOP_SUPERMARKET),
        "Central Wine Cellar": ("Tops Wine Cellar", "Q134932632", Categories.SHOP_WINE),
        "Tops": ("Tops", "Q7825140", Categories.SHOP_SUPERMARKET),
        "Tops Fine Food": ("Tops Fine Food", "Q134932619", Categories.SHOP_SUPERMARKET),
        "Tops Food Hall": ("Tops Food Hall", "Q134932513", Categories.SHOP_SUPERMARKET),
        "Tops market": ("Tops Market", "Q134932553", Categories.SHOP_SUPERMARKET),
    }

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("value"))

    # flake8: noqa: C901
    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["latitude"] or not feature["longitude"]:
            # Some features are blank (test features?)
            return
        if feature["store_format"] in ["Tops daily"]:
            # A different spider (tops_daily_th) already exists for this brand.
            return
        if feature["store_format"] not in self.brands.keys():
            # There's a few stores with a different format/name but they're
            # only once-off stores. Ignore these ~5 stores.
            return

        item["ref"] = str(item["ref"])
        item["brand"] = self.brands[feature["store_format"]][0]
        item["brand_wikidata"] = self.brands[feature["store_format"]][1]
        apply_category(self.brands[feature["store_format"]][2], item)

        # Most features have a Thai and English address listed. Sometimes
        # addresses are only provided in one language.
        item["addr_full"] = None
        if addr_full_th := feature["location"]:
            item["addr_full"] = addr_full_th
        if addr_full_en := feature["location_en"]:
            if not item["addr_full"]:
                item["addr_full"] = addr_full_en
            item["extras"]["addr_full:en"] = addr_full_en

        # There are lots of invalid-looking phone numbers (for example,
        # possibly a phone number followed by local extension code). Ignore
        # such numbers.
        item["phone"] = None
        if phone_number := feature["phone"]:
            if "N/A" not in phone_number:
                phone_number = re.sub(r"[\- ]+", "", phone_number).split(",", 1)[0].split("#", 1)[0]
                if len(phone_number) == 9:
                    item["phone"] = phone_number

        # Store name fields are jumbled up (country code is sometimes flipped).
        item.pop("name", None)
        if store_name_en := feature["store_name"]:
            if store_name_th := feature["store_name_th"]:
                if store_name_th.startswith("Tops ") and store_name_en.startswith("ท็อปส์ "):
                    store_name_en = feature["store_name_th"]
                    store_name_th = feature["store_name"]
                store_name_en = re.sub(r"\s+", " ", store_name_en)
                store_name_th = re.sub(r"\s+", " ", store_name_th)
                store_name_en = store_name_en.removeprefix("Tops Wine Cellar ").removeprefix("Tops Food Hall ").removeprefix("Tops Fine Food ").removeprefix("Tops ")
                store_name_th = store_name_th.removeprefix("ท็อปส์ ไวน์ เซลล่าร์ ").removeprefix("ท็อปส์ ฟู้ด ฮอลล์ ").removeprefix("ท็อปส์ ไฟน์ ฟู้ด ").removeprefix("ท็อปส์ ")
                if not store_name_en.startswith("ท็อปส์ ") and not store_name_th.startswith("Tops "):
                    item["branch"] = store_name_th
                    item["extras"]["branch:en"] = store_name_en

        # Opening hours information is a bit of a mess of freetext formats.
        # The below wrangling should get close to 100% extraction of hours.
        if hours_text := feature["operation_time"]:
            hours_text = hours_text.upper().replace("& HOLIDAY", "").replace(" AND HOLIDAY", "").replace("&HOLIDAY", "").replace("CLOSE ON SUNDAY AND PUBLIC HOLIDAY", " SUNDAY: CLOSED").replace("24 HRS", "00:01-23:59").replace("จ.- อา.", "MON-SUN")
            if "MON" not in hours_text and "SAT" not in hours_text and "SUN" not in hours_text:
                hours_text = f"MON-SUN: {hours_text}"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)

        yield item
