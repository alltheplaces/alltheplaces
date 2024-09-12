from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import clean_address

MR_PRICE_BRANDS = {
    "01": {"brand": "Mr Price", "brand_wikidata": "Q129561257"},
    "02": {"brand": "Mr Price Home", "brand_wikidata": "Q129561270"},
    "07": {"brand": "Mr Price Sport", "brand_wikidata": "Q129561262"},
}


class MrPriceSpider(Spider):
    name = "mr_price"
    start_urls = ["https://apiprd.omni.mrpg.com/graphql"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                method="POST",
                headers={"store": "en_za"},
                data={
                    "operationName": "StoreLocationByDivision",
                    "variables": {"division_id": ""},
                    "query": "query StoreLocationByDivision($division_id: String!) {\n  getStoreLocationByDivision(division_id: $division_id) {\n    ...StoreLocation\n    __typename\n  }\n}\n\nfragment StoreLocation on Store {\n  title\n  description\n  filterAttributes: filter_attributes {\n    attributeCode: attribute_code\n    __typename\n  }\n  companyStoreId: company_store_id\n  countryLocationId: country_location_id\n  physicalAddress1: address_line_1\n  physicalAddress2: address_line_2\n  physicalAddress3: address_line_3\n  postalCode: post_code\n  city\n  province\n  country\n  latitude\n  longitude\n  phone\n  weekDays: opening_hours_weekdays\n  saturdays: opening_hours_saturday\n  sundays: opening_hours_sunday\n  mondays: opening_hours_monday\n  tuesdays: opening_hours_tuesday\n  wednesdays: opening_hours_wednesday\n  thursdays: opening_hours_thursday\n  fridays: opening_hours_friday\n  __typename\n}\n",
                },
            )

    def parse(self, response):
        for location in response.json()["data"]["getStoreLocationByDivision"]:
            location["ref"] = location.pop("companyStoreId")
            location["street_address"] = clean_address(
                [location.pop("physicalAddress1"), location.pop("physicalAddress2"), location.pop("physicalAddress3")]
            )

            item = DictParser.parse(location)

            item.update(MR_PRICE_BRANDS.get(item["ref"][0:2]))
            item["branch"] = item.pop("name").replace(item["brand"], "").strip()

            oh = OpeningHours()
            if location.get("weekDays") is not None:
                oh.add_ranges_from_string("Mo-Fr " + location["weekDays"])
            else:
                for day in DAYS_FULL:
                    if location.get(day.lower() + "s") is not None:
                        oh.add_ranges_from_string(day + " " + location.get(day.lower() + "s"))
            item["opening_hours"] = oh.as_opening_hours()

            yield item
