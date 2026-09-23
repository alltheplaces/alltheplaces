from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response, TextResponse
from scrapy.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class LovesUSSpider(Spider):
    name = "loves_us"
    SPEEDCO = {"brand": "Speedco", "brand_wikidata": "Q112455073"}
    item_attributes = {"brand": "Love's", "brand_wikidata": "Q1872496"}
    allowed_domains = ["www.loves.com"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    PAGE_SIZE = 100
    AMENITIES = {
        "amazonpickup": Extras.PARCEL_PICKUP,
        "atm": Extras.ATM,
        "laundryfacilities": Extras.LAUNDRY,
        "overnightparking": Access.HGV,
        "privateshowers": Extras.SHOWERS,
        "rvdump": Extras.SANITARY_DUMP_STATION,
        "truckwash": Extras.TRUCK_WASH,
        "wirelessinternet": Extras.WIFI,
    }
    FUEL_TYPES = {
        "Bulk DEF": Fuel.ADBLUE,
        "CNG": Fuel.CNG,
        "Fast Fill CNG": Fuel.CNG,
        "Midgrade": Fuel.OCTANE_89,
        "Premium": Fuel.OCTANE_93,
        "Propane": Fuel.PROPANE,
        "Unleaded": Fuel.OCTANE_87,
    }

    canonical_urls = {}

    async def start(self) -> AsyncIterator[Any]:
        yield Request("https://www.loves.com/sitemap-locations.xml", callback=self.parse_sitemap)

    def parse_sitemap(self, response: Response, **kwargs: Any) -> Any:
        for url in iterloc(Sitemap(response.body)):
            if url.startswith("https://www.loves.com/locations/"):
                self.canonical_urls[url.rsplit("-", 1)[1]] = url

        yield self.page_request(0)

    def page_request(self, page_number: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.loves.com/api/search_stores",
            data={"pageNumber": page_number, "pageSize": str(self.PAGE_SIZE), "lat": 36.5489, "lng": -118.9127},
            cb_kwargs={"page_number": page_number},
        )

    def parse(self, response: TextResponse, page_number: int = 0) -> Iterable[Feature | JsonRequest]:
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["ref"] = store.get("number")
            item["branch"] = store["preferredName"]
            item["street_address"] = item.pop("addr_full", None)
            item["email"] = store["mainEmail"]
            item["website"] = "https://www.loves.com/locations/{}".format(store["number"])
            if store.get("number") and str(store["number"]) in self.canonical_urls:
                item["website"] = self.canonical_urls[str(store["number"])]

            if store["storeSearchData"]["name"] == "Speedco":
                item.update(self.SPEEDCO)
                apply_category(Categories.SHOP_TRUCK_REPAIR, item)
            elif store["storeSearchData"]["name"] == "Country Store":
                apply_category(Categories.FUEL_STATION, item)
            else:
                apply_category(Categories.HIGHWAY_SERVICES, item)

            custom_fields = store["mappedCustomFields"]
            item["opening_hours"] = OpeningHours()
            if store_hours := next(
                (
                    field["fieldValue"]
                    for field in custom_fields["facilityHoursOfOperation"]
                    if field["fieldName"] == "Store"
                ),
                None,
            ):
                for day in DAYS:
                    self.add_hours(item["opening_hours"], day, store_hours)
            for field in custom_fields["businessHours"]:
                self.add_hours(item["opening_hours"], field["fieldName"], field["fieldValue"])

            amenities = {field["smaFieldName"] for field in custom_fields["amenities"] if field["fieldValue"] == "true"}
            for amenity, tag in self.AMENITIES.items():
                apply_yes_no(tag, item, amenity in amenities)

            fuel_types = {fuel["fuelType"] for fuel in store["fuelPrices"]}
            for fuel_type, tag in self.FUEL_TYPES.items():
                apply_yes_no(tag, item, fuel_type in fuel_types)
            apply_yes_no(Fuel.DIESEL, item, any("Diesel" in fuel_type for fuel_type in fuel_types))
            apply_yes_no(
                Fuel.HGV_DIESEL, item, any(fuel_type.startswith(("Bio-Diesel", "Diesel")) for fuel_type in fuel_types)
            )
            apply_yes_no(Fuel.BIODIESEL, item, any(fuel_type.startswith("Bio-Diesel") for fuel_type in fuel_types))

            yield item

        if len(response.json()["stores"]) == self.PAGE_SIZE:
            yield self.page_request(page_number + 1)

    @staticmethod
    def add_hours(opening_hours: OpeningHours, day: str, hours: str) -> None:
        if hours.lower().startswith("open 24"):
            opening_hours.add_range(day, "00:00", "24:00")
        else:
            opening_hours.add_ranges_from_string("{} {}".format(day, hours))
