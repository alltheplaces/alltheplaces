from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.storepoint import StorepointSpider


class TouchstoneMedicalImagingUSSpider(StorepointSpider):
    name = "touchstone_medical_imaging_us"
    item_attributes = {
        "brand": "Touchstone Medical Imaging",
        "brand_wikidata": "Q123370518",
        "extras": {"amenity": "clinic", "healthcare": "clinic", "healthcare:speciality": "diagnostic_radiology"},
    }
    key = "1632ba0abb55f7"

    def parse_item(self, item, location):
        item["opening_hours"] = OpeningHours()
        hours_string = ""
        for day_name in DAYS_FULL:
            hours_range = location.get(day_name.lower(), "")
            hours_string = f"{hours_string} {day_name}: {hours_range}"
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
