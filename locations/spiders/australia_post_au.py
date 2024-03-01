import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class AustraliaPostAUSpider(scrapy.Spider):
    name = "australia_post_au"
    item_attributes = {"brand": "Australia Post", "brand_wikidata": "Q1142936"}

    def start_requests(self):
        for lat, lon in [
            (-29, 119),
            (-16, 125),
            (-21, 142),
            (-32, 142),
            (-28, 134),
            (-42, 148),
            (-28, 151),
        ]:
            yield JsonRequest(
                url=f"https://digitalapi.auspost.com.au/locations/v2/points/geo/{lon}/{lat}?radius=1000&types=C_SPB,DC,PO,R_SPB,UPL&limit=10000",
                headers={"AUTH-KEY": "jAgsMKkO3rOQ3OP60sIegEiAj1yrhVqi"},
            )

    def parse(self, response, **kwargs):
        for store in response.json()["points"]:
            item = DictParser.parse(store)
            item["ref"] = store["location_code"]
            item["street_address"] = merge_address_lines(
                [store.get("address_line_1"), store.get("address_line_2"), store.get("address_line_3")]
            )
            item["opening_hours"] = OpeningHours()
            for i in store["hours"]:
                if i["type"] in ["CLOSED", "SPECIAL_CLOSED", "Closed", "SPECIAL_LUNCH", "", None]:
                    continue
                day = DAYS[int(i["weekday"])]
                open_time = i["start_time"]
                close_time = i["end_time"]
                if close_time == "23:59:59":
                    close_time = "23:59"
                    item["opening_hours"].add_range(day, open_time.strip(), close_time.strip())

            if store["type"] == "C_SPB":
                apply_category(Categories.POST_BOX.value | {"priority": "yes"}, item)
            elif store["type"] == "DC":
                apply_category(Categories.POST_DEPOT, item)
            elif store["type"] == "PO":
                apply_category(Categories.POST_OFFICE, item)
            elif store["type"] == "R_SPB":
                apply_category(Categories.POST_BOX, item)
            elif store["type"] == "UPL":
                apply_category(Categories.PARCEL_LOCKER, item)

            yield item
