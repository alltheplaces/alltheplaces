from copy import deepcopy
from datetime import timedelta
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaHawaiiTerritoriesUSSpider(Spider):
    name = "toyota_hawaii_territories_us"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES

    async def start(self) -> AsyncIterator[Request]:
        # U.S. Virgin Islands and Puerto Rico
        yield Request(
            url="https://ikfta7p4uj.execute-api.us-east-1.amazonaws.com/Development/getDealersProduction?city=San%20Juan&state=PR",
            callback=self.parse_us_territories,
        )
        # Hawaii
        yield Request(url="https://www.toyotahawaii.com/find-a-dealer", callback=self.parse_hawaii)

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

                if department_name == "Main Dealer":
                    yield self.build_shop(feature, item)

                elif department_name == "Service":
                    yield self.build_service(feature, item)

                elif department_name == "Parts":
                    yield self.build_parts(feature, item)

    def parse_hawaii(self, response: Response, **kwargs: Any) -> Any:
        for dealer in response.xpath("//label[@class='mb-4 radioLabel']"):
            item = Feature()
            item["ref"] = dealer.xpath(".//input/@value").get()
            item["name"] = dealer.xpath(".//input/@data-storename").get()
            item["lat"] = dealer.xpath(".//input/@data-lat").get()
            item["lon"] = dealer.xpath(".//input/@data-lng").get()
            item["addr_full"] = dealer.xpath(".//a[contains(@class, 'dealer-info')][1]/text()").get()
            item["phone"] = dealer.xpath(".//a[contains(@class, 'dealer-info')][2]/text()").get()
            item["website"] = dealer.xpath(".//span[@class='store-links']/a/@href").get()
            # All locations appear to offer both sales and service.
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-SHOP"
            apply_category(Categories.SHOP_CAR, shop_item)
            yield shop_item
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

    def build_shop(self, feature: dict, item: Feature) -> Feature:
        shop_item = deepcopy(item)
        shop_item["ref"] = f"{item['ref']}-SHOP"
        self.parse_hours(shop_item, feature, "Sales")
        apply_category(Categories.SHOP_CAR, shop_item)
        return shop_item

    def build_service(self, feature: dict, item: Feature) -> Feature:
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-SERVICE"
        self.parse_hours(service_item, feature, "Service")
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def build_parts(self, feature: dict, item: Feature) -> Feature:
        parts_item = deepcopy(item)
        parts_item["ref"] = f"{item['ref']}-PARTS"
        self.parse_hours(parts_item, feature, "Parts")
        apply_category(Categories.SHOP_CAR_PARTS, parts_item)
        return parts_item

    def parse_hours(self, item: Feature, feature: dict, location_type: str) -> None:
        try:
            oh = OpeningHours()
            hours_list = []
            for hours_type in feature.get("hoursOfOperation", []):
                if hours_type["hoursTypeCode"] == location_type:
                    hours_list = hours_type["daysOfWeek"]
                    break
            for day_times in hours_list:
                if "availabilityStartTimeMeasure" in day_times:
                    units_start = day_times["availabilityStartTimeMeasure"]["unitCode"]
                    units_end = day_times["availabilityEndTimeMeasure"]["unitCode"]
                    if units_start == "MINUTE" and units_end == "MINUTE":
                        oh.add_range(
                            day_times["dayOfWeekCode"],
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
