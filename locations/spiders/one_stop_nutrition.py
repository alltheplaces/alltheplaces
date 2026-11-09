import re
from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

# The map the chain's locations page embeds.
MARKERS = "https://api.atlist.com/v1/map/077a4f85-31be-4593-b570-7a530d69a826/markers"
# "18255 N 83rd Ave suite 103, Glendale, AZ 85308, USA"
ADDRESS = re.compile(
    r"^(?P<street>.+),\s*(?P<city>[^,]+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})(?:-\d{4})?,\s*USA\s*$"
)
PHONE = re.compile(r"\(?\d{3}\)?[ .-]?\d{3}[-.]\d{4}")
# A shop that has not opened yet says so in its name.
NOT_OPEN_YET = re.compile(r"coming\s*soon", re.IGNORECASE)


class OneStopNutritionSpider(JSONBlobSpider):
    """The chain's locations page is a map, and the map states every shop.

    Each shop carries its hours and telephone number as a little web page of
    its own inside the marker, which is read for them.
    """

    name = "one_stop_nutrition"
    # Neither the chain nor any of its shops has a Wikidata item. The One Stop
    # that does is a chain of convenience shops in Britain and not this.
    item_attributes = {"brand": "One Stop Nutrition"}
    allowed_domains = ["api.atlist.com"]
    start_urls = [MARKERS]
    locations_key = "markers"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        name = (feature.get("name") or "").strip()
        if NOT_OPEN_YET.search(name):
            self.logger.info(f"{name} has not opened yet, so it is not published")
            return

        item["ref"] = feature.get("id")
        item.pop("name", None)
        item["lat"], item["lon"] = feature.get("lat"), feature.get("long")

        # The whole address is stated in one line, which is taken apart below,
        # so it is not also kept as it came.
        item.pop("addr_full", None)

        stated = feature.get("formattedAddress") or ""
        if address := ADDRESS.match(stated):
            item["street_address"] = address["street"]
            item["city"] = address["city"]
            item["state"] = address["state"]
            item["postcode"] = address["postcode"]
            item["country"] = "US"
        else:
            self.logger.warning(f"Unparsed address {stated!r} for {name}")

        item["branch"] = self.spoken(name, item.get("state"))

        told = self.notes(feature)
        if phone := PHONE.search(told):
            item["phone"] = phone.group()
        item["opening_hours"] = self.parse_hours(told)

        if place := feature.get("placeId"):
            item["extras"]["ref:google:place_id"] = place

        apply_category(Categories.SHOP_NUTRITION_SUPPLEMENTS, item)
        yield item

    @staticmethod
    def notes(feature: dict) -> str:
        """Return the words of the page a marker carries inside it."""
        if not (notes := feature.get("notes")):
            return ""
        return " ".join(filter(None, map(str.strip, Selector(text=notes).xpath("//text()").getall())))

    def parse_hours(self, told: str) -> OpeningHours:
        oh = OpeningHours()
        if told:
            oh.add_ranges_from_string(told, days=DAYS_EN)
        return oh

    @staticmethod
    def spoken(name: str, state: str | None = None) -> str | None:
        """Take the shouting out of a name, which is published in capitals.

        The shops are named for their crossroads, as "ARCADIA-44TH ST/INDIAN
        SCHOOL", so each run of letters is given a capital of its own and then
        the few sorts of word that do not want one are put back.
        """
        if not name:
            return None
        spoken = re.sub(r"[^\W\d_]+", lambda run: run.group().capitalize(), name)
        # An ordinal goes back down: "83Rd Ave" to "83rd Ave".
        spoken = re.sub(r"(?<=\d)(St|Nd|Rd|Th)\b", lambda suffix: suffix.group().lower(), spoken)
        # A road keeps its number's prefix in capitals: "Us-60" to "US-60".
        spoken = re.sub(r"\b(Us|Sr)(?=-\d)", lambda prefix: prefix.group().upper(), spoken)
        # A name of this sort carries a capital of its own: "McKellips".
        spoken = re.sub(r"\bMc([a-z])", lambda letter: "Mc" + letter.group(1).upper(), spoken)
        # The few shops outside Arizona name their state, as "Southlake TX".
        if state:
            spoken = re.sub(rf"\b{re.escape(state)}$", state.upper(), spoken, flags=re.IGNORECASE)
        return spoken or None
