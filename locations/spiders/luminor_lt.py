import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class LuminorLTSpider(Spider):
    name = "luminor_lt"
    item_attributes = {"brand": "Luminor Bank", "brand_wikidata": "Q28966957"}
    requires_proxy = True
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.luminor.lt/en/bank-network"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not (contacts := self.extract_page_contacts(response)):
            self.logger.error("Unable to find Luminor contacts data")
            return

        for ref, location in contacts.get("map_objects", {}).items():
            object_types = {str(object_type) for object_type in location.get("object_types", [])}
            has_branch = "74" in object_types
            has_atm = location.get("pin_icon") in ["cash-out", "cash-in-out", "partner"] or bool(
                {"70", "71", "75"} & object_types
            )
            if not (has_branch or has_atm):
                continue

            # Source map settings nest coordinates and town names, so DictParser cannot map the useful fields.
            item = Feature(
                ref=ref,
                branch=self.clean_branch(location.get("title")),
                lat=location.get("geolocation", {}).get("lat"),
                lon=location.get("geolocation", {}).get("lng"),
                street_address=location.get("address"),
                city=self.get_city(location, contacts),
            )

            if has_branch:
                apply_yes_no(Extras.ATM, item, has_atm)
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)

            yield item

    def extract_page_contacts(self, response: Response) -> dict[str, Any] | None:
        settings_marker = "jQuery.extend(Drupal.settings,"
        if (settings_start := response.text.find(settings_marker)) == -1:
            return None
        data_start = response.text.find("{", settings_start)
        if data_start == -1:
            return None

        settings, _ = json.JSONDecoder().raw_decode(response.text[data_start:])
        return settings.get("dnb_contacts")

    def clean_branch(self, branch: str | None) -> str | None:
        if not branch:
            return None
        return branch.split("|", 1)[0].strip()

    def get_city(self, location: dict[str, Any], contacts: dict[str, Any]) -> str | None:
        town = location.get("town", {})
        towns = contacts.get("towns_tree") or contacts.get("towns") or {}
        county = self.get_town(towns, town.get("county"))
        if not county:
            return None
        if child := self.get_town(county.get("children", []), town.get("town")):
            return child.get("name")
        return None

    def get_town(self, towns: Any, town_id: Any) -> dict[str, Any] | None:
        if town_id is None:
            return None
        if isinstance(towns, dict):
            return towns.get(str(town_id)) or towns.get(town_id)
        if isinstance(towns, list):
            for town in towns:
                if str(town.get("id")) == str(town_id):
                    return town
        return None
