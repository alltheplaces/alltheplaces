import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class EasyPointTRSpider(scrapy.Spider):
    name = "easy_point_tr"
    # create a wikidata item for the brand
    item_attributes = {"brand": "Easy Point", "brand_wikidata": "Q131451912"}

    def start_requests(self):
        yield JsonRequest(
            "https://prod.easypointapi.com/api/get-token",
            method="POST",
            data={
                "key": "wHjOKqH25WwOEeHphyGR",
                "secret": "37m2LWciLhboNNFA6UkQ",
            },
            callback=self.parse_token,
        )

    def parse_token(self, response):
        resp = response.json()
        token = resp["result"]["token"]

        yield scrapy.Request(
            "https://prod.easypointapi.com/api/flow/get-points",
            method="POST",
            headers={"Authorization": f"Bearer {token}"},
            callback=self.parse,
        )

    def parse(self, response):
        for item in response.json()["result"]:
            d = DictParser.parse(item)
            d["opening_hours"] = parse_opening_hours(item["workingDays"])
            if d["phone"] or d["phone"] == "":
                d["phone"] = item.get("userPhone")

            # Turkish address fields tend to be wrongly named in the API
            d["state"] = item["city"]  # province/il in Turkish
            d["city"] = item["district"]  # district/ilçe in Turkish
            d["addr_full"] = f"{item['muhaberatAddress1']} {item['district']} {item['city']}"
            apply_category({"addr:neighborhood": item["region"]}, d)  # mahalle in Turkish
            apply_category({"addr:desc": item["pointAddressDefinition"]}, d)

            if bool(int(item["isBox"])):
                apply_category(Categories.PARCEL_LOCKER, d)
                apply_category({"post_office:parcel_pickup": parse_parcel_from(item)}, d)

            elif bool(int(item["isEsnaf"])):
                apply_category({"post_office:service_provider": self.item_attributes["brand"]}, d)
                apply_category({"post_office": "post_partner"}, d)
                apply_category({"post_office:parcel_pickup": parse_parcel_from(item)}, d)

            elif bool(int(item["isMalKabul"])):
                apply_category({"amenity": "delivery_area"}, d)

            else:
                apply_category({"post_office:service_provider": self.item_attributes["brand"]}, d)
                apply_category({"post_office": "post_partner"}, d)
                apply_category({"post_office:parcel_pickup": parse_parcel_from(item)}, d)

            apply_category({"capacity:package": item["packageCapacity"]}, d)

            yield d


def parse_opening_hours(item: dict) -> str:
    keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    oh = OpeningHours()
    for key in keys:
        if key not in item:
            continue
        day_entry = item.get(key)
        if day_entry and day_entry.get("enable"):
            open_time_dict = day_entry["openingTime"]
            closed_time_dict = day_entry["closingTime"]

            open_time = get_time_str(open_time_dict)
            close_time = get_time_str(closed_time_dict)

            if open_time and close_time:
                oh.add_range(day=key[:2].capitalize(), open_time=open_time, close_time=close_time)

    return oh.as_opening_hours()


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
