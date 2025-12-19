from copy import deepcopy
from datetime import timedelta
from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaUSSpider(JSONBlobSpider):
    name = "toyota_us"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    locations_key = "dealers"
    requires_proxy = True

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        # API can not handle huge radius coverage, therefore
        # I decicded to use zipcodes from:
        # Alaska(99775), Florida(33040), California(91932), Washington(98221), Kansas(66952), Maine(04619)
        for zip_code in ["99775", "33040", "91932", "98221", "66952", "04619"]:
            yield Request(
                url=f"https://api.ws.dpcmaps.toyota.com/v1/dealers?searchMode=pmaProximityLayered&radiusMiles=1000&resultsMax=5000&zipcode={zip_code}",
            )

        # U.S. Virgin Islands and Puerto Rico
        yield Request(
            url="https://ikfta7p4uj.execute-api.us-east-1.amazonaws.com/Development/getDealersProduction?city=San%20Juan&state=PR",
            callback=self.parse_us_territories,
        )

        # Hawaii
        yield Request(url="https://www.toyotahawaii.com/find-a-dealer", callback=self.parse_hawaii)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        full_address = item.pop("addr_full")
        location = [item.strip() for item in full_address.split(",")]
        item["street_address"] = location[0]
        item["city"] = location[1]
        item["postcode"] = location[len(location) - 1].split(" ")[1]
        item["name"] = feature["label"]
        item["website"] = feature["details"]["uriWebsite"]
        self.parse_hours(item, feature["hoursOfOperation"])
        departments = feature["details"]["departmentInformation"]
        shop_item = self.build_shop(item)
        apply_yes_no(Extras.CAR_PARTS, shop_item, "Parts" in departments)
        yield shop_item
        if "Service" in departments:
            yield self.build_service(item)

    def parse_us_territories(self, response: Response, **kwargs: Any) -> Any:
        features = response.json()["showDealerLocatorDataArea"]["dealerLocator"][0]["dealerLocatorDetail"]

        def parse_contacts(contacts: list[dict], label: str) -> str:
            for contact in contacts:
                if contact["channelCode"]["value"] == label:
                    if phone := contact.get("completeNumber"):
                        return phone["value"]
                    elif social := contact.get("uriid"):
                        return social["value"]

        for feature in features:
            item = Feature()
            item["ref"] = feature["dealerParty"]["partyID"]["value"]
            item["name"] = feature["dealerParty"]["specifiedOrganization"]["companyName"]["value"]
            item["lat"] = feature["proximityMeasureGroup"]["geographicalCoordinate"]["latitudeMeasure"]["value"]
            item["lon"] = feature["proximityMeasureGroup"]["geographicalCoordinate"]["longitudeMeasure"]["value"]
            address = feature["dealerParty"]["specifiedOrganization"]["postalAddress"]
            item["street_address"] = address["lineOne"]["value"]
            item["city"] = address["cityName"]["value"]
            item["state"] = address["stateOrProvinceCountrySubDivisionID"]["value"]
            item["postcode"] = address["postcode"]["value"]
            item["country"] = "US"
            departments = feature["dealerParty"]["specifiedOrganization"]["primaryContact"]

            for department in departments:
                department_name = department["departmentName"]["value"]

                if phones := department.get("telephoneCommunication"):
                    item["phone"] = parse_contacts(phones, "Phone")
                    item["extras"]["fax"] = parse_contacts(phones, "Fax")

                if socials := department.get("uricommunication"):
                    item["website"] = parse_contacts(socials, "Website")
                    item["email"] = parse_contacts(socials, "Email")

                self.parse_hours(item, feature["hoursOfOperation"][0]["daysOfWeek"])

                if department_name == "Main Dealer":
                    yield self.build_shop(item)

                elif department_name == "Service":
                    yield self.build_service(item)

    def parse_hawaii(self, response: Response, **kwargs: Any) -> Any:
        dealers = response.xpath("//label[@class='mb-4 radioLabel']")
        for dealer in dealers:
            item = Feature()
            item["ref"] = dealer.xpath(".//input/@value").get()
            item["name"] = dealer.xpath(".//input/@data-storename").get()
            item["lat"] = dealer.xpath(".//input/@data-lat").get()
            item["lon"] = dealer.xpath(".//input/@data-lng").get()
            item["addr_full"] = dealer.xpath(".//a[contains(@class, 'dealer-info')][1]/text()").get()
            item["phone"] = dealer.xpath(".//a[contains(@class, 'dealer-info')][2]/text()").get()
            item["website"] = dealer.xpath(".//span[@class='store-links']/a/@href").get()
            yield self.build_shop(item)

    def build_shop(self, item: Feature) -> Feature:
        shop_item = deepcopy(item)
        shop_item["ref"] = f"{item['ref']}-SHOP"
        apply_category(Categories.SHOP_CAR, shop_item)
        return shop_item

    def build_service(self, item: Feature) -> Feature:
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-SERVICE"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def parse_hours(self, item, hours_type):
        try:
            oh = OpeningHours()
            for day_times in hours_type:
                if "availabilityStartTimeMeasure" in day_times:
                    units_start = day_times["availabilityStartTimeMeasure"]["unitCode"]
                    units_end = day_times["availabilityEndTimeMeasure"]["unitCode"]
                    if units_start == "MINUTE" and units_end == "MINUTE":
                        oh.add_range(
                            day_times["dayOfWeekCode"][:2],
                            str(timedelta(minutes=day_times["availabilityStartTimeMeasure"]["value"])),
                            str(timedelta(minutes=day_times["availabilityEndTimeMeasure"]["value"])),
                            time_format="%H:%M:%S",
                        )
                    else:
                        self.crawler.stats.inc_value(f"atp/{self.name}/unknown_time_unit/{units_start}/{units_end}")
                else:
                    oh.set_closed(day_times["dayOfWeekCode"])

            if len(oh.day_hours) > 0:
                item["opening_hours"] = oh

        except Exception as e:
            self.logger.error(f"Error during parsing hours for {item['ref']}: {e}")
            self.crawler.stats.inc_value(f"atp/{self.name}/error_during_parse_hours/{item['ref']}")
