from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

LOCATOR_NL = "https://www.qteam.be/nl/onze-service-centers/"
LOCATOR_FR = "https://www.qteam.be/fr/nos-centres-de-service/"

SERVICES = {
    "WsAlign": Extras.VEHICLE_WHEEL_ALIGNMENT_SERVICES,
    "WsBatteries": Extras.VEHICLE_BATTERY_SERVICES,
    "WsBrakes": Extras.VEHICLE_BRAKE_SERVICES,
    "WsOil": Extras.VEHICLE_OIL_CHANGE_SERVICES,
    "WsShockAbsorbers": Extras.VEHICLE_SUSPENSION_SERVICES,
    "WsTiresCars": Extras.VEHICLE_TYRE_SERVICES,
}


# ImageUrl is not mapped: the paths look per-depot, but 45 of the 104 published
# centres are served a photo of a different branch, either a shared default or
# one of three pictures reused across 22, 13 and 2 depots.
class QTeamBESpider(JSONBlobSpider):
    name = "q_team_be"
    item_attributes = {"brand": "QTeam", "brand_wikidata": "Q127691554", "name": "QTeam"}
    allowed_domains = ["www.qteam.be"]
    start_urls = ["https://www.qteam.be/api/searchgarage/getgaragesbycity"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The API reads the Referer: without one it returns no store page URLs.
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                method="POST",
                data={"PageSize": 1000},
                headers={"Referer": LOCATOR_NL},
            )

    def extract_json(self, response: Response) -> list[dict]:
        # The Dutch locator also returns legacy and fleet partner rows on top of the
        # published service centres, which WsWebsite marks. A published centre always
        # lists opening hours; the lone exception is a depot the source itself says has
        # relocated, and it offers no services either.
        return [garage for garage in response.json()["Garages"] if garage["WsWebsite"] and garage["OpeningHours"]]

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("Depot")
        feature["street_address"] = " ".join(feature.pop("Address").split())
        feature["city"] = feature.pop("Location")
        feature["postcode"] = str(feature.pop("Zip"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("QTeam").strip(" -")
        item["operator"] = feature["OfficialName"]
        item["website"] = response.urljoin(feature["Url"])
        # Each centre has a page in both languages, reachable by swapping the
        # localised path. One of the 104 uses a slightly different slug in French
        # and answers with a redirect to it rather than directly.
        item["extras"]["website:fr"] = item["website"].replace(LOCATOR_NL, LOCATOR_FR)

        item["opening_hours"] = OpeningHours()
        for rule in feature["OpeningHours"]:
            item["opening_hours"].add_range(DAYS[rule["Day"] - 1], rule["From"], rule["Until"])

        apply_category(Categories.SHOP_TYRES, item)
        apply_yes_no("car:tyres", item, feature["WsTiresCars"])
        apply_yes_no("truck:tyres", item, feature["WsTiresTrucks"])
        for key, service in SERVICES.items():
            apply_yes_no(service, item, feature[key])

        yield item
