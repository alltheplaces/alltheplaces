from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours

EASY_POINT = {"brand": "Easy Point", "brand_wikidata": "Q131451912"}


class EasyPointTRSpider(Spider):
    name = "easy_point_tr"

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            "https://prod.easypointapi.com/api/get-token",
            data={
                "key": "wHjOKqH25WwOEeHphyGR",
                "secret": "37m2LWciLhboNNFA6UkQ",
            },
            callback=self.parse_token,
        )

    def parse_token(self, response: Response, **kwargs: Any) -> Any:
        resp = response.json()
        token = resp["result"]["token"]

        yield JsonRequest(
            "https://prod.easypointapi.com/api/flow/get-points",
            method="POST",
            headers={"Authorization": f"Bearer {token}"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for item in response.json()["result"]:
            # fix malformed coordinates before giving it to the parser
            item["latitude"] = parse_float_like_coordinate(item["latitude"])
            item["longitude"] = parse_float_like_coordinate(item["longitude"])

            d = DictParser.parse(item)
            d["opening_hours"] = parse_opening_hours(item["workingDays"])
            if d["phone"] or d["phone"] == "":
                d["phone"] = item.get("userPhone")

            # Turkish address fields tend to be wrongly named in the API
            d["state"] = item["city"]  # province/il in Turkish
            d["city"] = item["district"]  # district/ilçe in Turkish
            d["street_address"] = item["muhaberatAddress1"]
            d["addr_full"] = f"{item['muhaberatAddress1']} {item['district']} {item['city']}"
            d["extras"]["addr:neighborhood"] = item["region"]  # mahalle in Turkish
            d["extras"]["addr:desc"] = item["pointAddressDefinition"]

            if bool(int(item["isBox"])):
                d.update(EASY_POINT)
                apply_category(Categories.PARCEL_LOCKER, d)
                d["extras"]["post_office:parcel_pickup"] = parse_parcel_from(item)

            elif bool(int(item["isEsnaf"])):
                apply_category(Categories.GENERIC_POI, d)
                d["extras"]["post_office"] = "post_partner"
                d["extras"]["post_office:service_provider"] = EASY_POINT["brand"]
                d["extras"]["post_office:parcel_pickup"] = parse_parcel_from(item)

            elif bool(int(item["isMalKabul"])):
                apply_category({"amenity": "delivery_area"}, d)

            else:
                apply_category(Categories.GENERIC_POI, d)
                d["extras"]["post_office"] = "post_partner"
                d["extras"]["post_office:service_provider"] = EASY_POINT["brand"]
                d["extras"]["post_office:parcel_pickup"] = parse_parcel_from(item)

            d["extras"]["capacity:package"] = item["packageCapacity"]

            yield d


def parse_opening_hours(item: dict) -> str:
    oh = OpeningHours()
    for key in map(str.lower, DAYS_FULL):
        if key not in item:
            continue
        day_entry = item.get(key)
        if day_entry and day_entry.get("enable"):
            open_time_dict = day_entry["openingTime"]
            closed_time_dict = day_entry["closingTime"]

            open_time = get_time_str(open_time_dict)
            close_time = get_time_str(closed_time_dict)

            if open_time and close_time:
                oh.add_range(day=key, open_time=open_time, close_time=close_time)

    return oh


def get_time_str(time_dict: dict) -> str | None:
    if (
        time_dict["hour"] is None
        or time_dict["minute"] is None
        or time_dict["hour"] == "-1"
        or time_dict["minute"] == "-1"
    ):
        return None
    return f"{time_dict['hour']}:{time_dict['minute']}"


def parse_parcel_from(item: dict) -> str:
    field_to_company = {
        "isAmazon": "Amazon",
        "isHepsiburada": "Hepsiburada",
        "isN11": "N11",
        "isTrendyol": "Trendyol",
        "isHepsiJet": "HepsiJet",
        "isArasKargo": "Aras Kargo",
        "is_suratkargo": "Sürat Kargo",
    }

    companies = []

    for field, company in field_to_company.items():
        try:
            if bool(int(item[field])):
                companies.append(company)
        except (KeyError, ValueError):
            continue

    text = "; ".join(companies)

    if text == "":
        return "yes"
    else:
        return text


def parse_float_like_coordinate(coord: str) -> float | None:
    if coord == "":
        return None
    allowed_chars = "0123456789.,"
    cleaned_coord = "".join(filter(lambda char: char in allowed_chars, coord))

    if cleaned_coord == "":
        return None

    cleaned2_chars = []
    added_decimal_point = False
    for i, char in enumerate(cleaned_coord):
        if char in ",.":
            if (
                i == 0  # first char cannot be a separator
                or i == len(cleaned_coord) - 1  # last char cannot be a separator
                or cleaned_coord[i - 1] == ","  # cannot have two separators in a row
            ):
                continue
            if not added_decimal_point:
                cleaned2_chars.append(".")
                added_decimal_point = True
        else:
            cleaned2_chars.append(char)

    return float("".join(cleaned2_chars))
