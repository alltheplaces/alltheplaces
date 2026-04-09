import re

from locations.categories import Categories, apply_category
from locations.hours import DAYS_BG, OpeningHours, sanitise_day
from locations.storefinders.virtualearth import VirtualEarthSpider


def transliterate(text):
    cyrillic_to_latin = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "'": "'",
        "ъ": "y",
        "ь": "'",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        ".": "",
        " ": "-",
    }
    return text.translate(str.maketrans(cyrillic_to_latin))


class LidlBGSpider(VirtualEarthSpider):
    name = "lidl_bg"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q108169047"}

    dataset_id = "04982a582660451a8e08b705855a1008"
    dataset_name = "Filialdaten-BG/Filialdaten-BG"
    api_key = "AkK9Xgxa6n1ly8c3xz1ntR6ojGGT3h-hys5yW7P9xHpJS2FycVLoYxLo_eeFR69o"

    def parse_item(self, item, feature, **kwargs):
        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+)\s+(\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_BG):
                item["opening_hours"].add_range(day, start_time, end_time)

        if item["city"] and item["street_address"]:
            city = transliterate(item["city"].lower())
            street = transliterate(item["street_address"].lower())
            item["website"] = f"https://www.lidl.bg/s/bg-BG/magazini/{city}/{street}/"

        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
