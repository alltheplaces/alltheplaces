from typing import AsyncIterator

from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class AscensionUSSpider(Spider):
    name = "ascension_us"
    item_attributes = {"brand": "Ascension", "brand_wikidata": "Q96372437", "nsi_id": "N/A"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    categories = {
        "Cancer Care": {"amenity": "clinic", "healthcare": "clinic", "healthcare:speciality": "oncology"},
        "Emergency Care": {"amenity": "clinic", "healthcare": "clinic", "healthcare:speciality": "emergency"},
        "Emergency Care - Pediatrics": Categories.CLINIC_URGENT.value
        | {"healthcare:speciality": "emergency;paediatrics"},
        "Hospital/Medical Center": Categories.HOSPITAL,
        "Imaging": {"amenity": "clinic", "healthcare": "clinic", "healthcare:speciality": "diagnostic_radiology"},
        "Laboratory": {"healthcare": "laboratory"},
        "Mammography": None,
        "Mental Health": None,
        "Pediatrics": {"amenity": "clinic", "healthcare": "clinic", "healthcare:speciality": "paediatrics"},
        "Pharmacy": Categories.PHARMACY,
        "Physical Therapy": {"amenity": "clinic", "healthcare": "clinic", "healthcare:speciality": "physiatry"},
        "Primary Care/Clinic": None,
        "Specialty Care": None,
        "Urgent or Express Care": Categories.CLINIC_URGENT,
        "Other": None,
    }

    @staticmethod
    def make_request(page: int, page_size: int = 100) -> JsonRequest:
        return JsonRequest(
            url="https://healthcare.ascension.org/api/locations/search",
            data={"geoDistanceOptions": {"location": "AL", "radius": 50000}, "page": page, "pageSize": page_size},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response, **kwargs):
        for result in response.json()["Results"]:
            location = result["Data"]["Location"]
            location["Address"]["street_address"] = merge_address_lines(
                [location["Address"].pop("Street"), location["Address"].pop("Street2")]
            )
            item = DictParser.parse(location)
            item["lat"] = location["Address"]["Latitude"]
            item["lon"] = location["Address"]["Longitude"]
            item["website"] = response.urljoin(location["Url"])

            if thumb := location.get("LocationThumbnail"):
                item["image"] = response.urljoin(thumb)

            if location["LocationTypeTags"] and (cat := self.categories.get(location["LocationTypeTags"][0])):
                apply_category(cat, item)
            else:
                apply_category({"amenity": "clinic", "healthcare": "clinic"}, item)

            yield item

        pagination = response.json()["Pagination"]
        if pagination["CurrentPage"] < pagination["TotalPages"]:
            yield self.make_request(pagination["CurrentPage"] + 1)
