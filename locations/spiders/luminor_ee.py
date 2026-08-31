from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class LuminorEESpider(Spider):
    name = "luminor_ee"
    item_attributes = {"brand": "Luminor Bank", "brand_wikidata": "Q28966957"}
    # luminor.ee is behind Cloudflare (403 to datacenter IPs); the /kontaktid contacts page is
    # rendered client-side from this JSON document.
    contacts_url = "https://luminor.ee/dc/render/v1/ee/page?alias=%2Fkontaktid&language=et"
    requires_proxy = True
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url=self.contacts_url)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not (contacts := self.extract_contacts(response)):
            self.logger.error("Unable to find Luminor contacts data")
            return

        object_types = contacts["object_types"]  # {"36": {"type": "branch", ...}, "34": {"type": "atm", ...}}
        towns = self.town_names(contacts.get("towns") or {})

        for location in contacts["objects"]:
            type_ids = location.get("object_types") or []
            kinds = {object_types.get(str(type_id), {}).get("type") for type_id in type_ids}
            if not kinds & {"branch", "atm"}:
                continue

            item = DictParser.parse(location)  # maps title->name, geolocation->lat/lon, address->addr_full
            item["ref"] = item.get("name")  # feed has no id; the venue/branch title is unique across the dataset
            item["street_address"] = item.pop("addr_full", None)
            item["city"] = towns.get((location.get("town") or {}).get("town"))  # DictParser leaves the raw id dict

            if "branch" in kinds:
                item["branch"] = item.pop("name")  # NSI supplies name=Luminor Bank
                apply_yes_no(Extras.ATM, item, "atm" in kinds)  # branches co-host ATMs; keep as one POI
                item["opening_hours"] = self.parse_hours(location, self.types_of_kind(object_types, type_ids, "branch"))
                apply_category(Categories.BANK, item)
            else:
                # A "raha sisse ja välja" (cash in and out) ATM is deposit-capable; "raha välja" is withdrawal only.
                cash_in = any("sisse" in object_types.get(str(type_id), {}).get("title", "") for type_id in type_ids)
                apply_yes_no(Extras.CASH_IN, item, cash_in)
                item["opening_hours"] = self.parse_hours(location, self.types_of_kind(object_types, type_ids, "atm"))
                apply_category(Categories.ATM, item)

            yield item

    @staticmethod
    def extract_contacts(response: Response) -> dict[str, Any] | None:
        for container in response.json().get("containers", []):
            for widget in container.get("widgets", []):
                contacts = (widget.get("widget_settings") or {}).get("contacts")
                if isinstance(contacts, dict) and "objects" in contacts:
                    return contacts
        return None

    @staticmethod
    def types_of_kind(object_types: dict, type_ids: list, kind: str) -> list:
        return [type_id for type_id in type_ids if object_types.get(str(type_id), {}).get("type") == kind]

    @staticmethod
    def town_names(towns: dict) -> dict:
        names = {}
        for county in towns.values():
            names[county.get("id")] = county.get("name")
            for child in county.get("children") or []:
                names[child.get("id")] = child.get("name")
        return names

    def parse_hours(self, location: dict, type_ids: list) -> str | None:
        working_time = location.get("working_time") or {}
        hours = OpeningHours()
        for type_id in type_ids:
            for entry in working_time.get(str(type_id)) or []:
                day, start, end = (
                    (entry or {}).get("day"),
                    (entry or {}).get("starthours"),
                    (entry or {}).get("endhours"),
                )
                if day is None or start is None or end is None:
                    continue
                end = 2400 if end == 0 else end  # a midnight closing time is encoded as 0
                try:
                    hours.add_range(DAYS[day], self.as_time(start), self.as_time(end))
                except (ValueError, IndexError):
                    continue
        return hours.as_opening_hours() or None

    @staticmethod
    def as_time(value: int) -> str:
        hours, minutes = divmod(value, 100)
        return "{:02d}:{:02d}".format(hours, minutes)
