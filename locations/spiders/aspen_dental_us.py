import re

from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

QUERY = """query bffFacilities($brand: BffBrandType!, $take: Int!, $skip: Int!) {
  facilityCollection(brand: $brand, take: $take, skip: $skip) {
    items {
      ...BffFacilityFields
    }
  }
}

fragment BffFacilityFields on BffFacility {
  name
  code
  phoneNumber
  address {
    ...BffFacilityAddress
  }
  location {
    ...BffFacilityLocation
  }
  workingHours {
    ...BffWorkingHours
  }
  openDate
}

fragment BffFacilityAddress on BffFacilityAddress {
  address1
  address2
  city
  stateCode
  zipCode
}

fragment BffFacilityLocation on BffFacilityLocation {
  latitude
  longitude
}

fragment BffWorkingHours on BffWorkingHours {
  date
  open {
    ...BffTimeSpan
  }
}

fragment BffTimeSpan on BffTimeSpan {
  from
  to
}"""


def generate_facility_url(state, city, line1):
    # adapted from src/utils/generateFacilityUrl.ts in site code
    if not state or not city or not line1:
        return None

    _state = state.lower()
    _city = city.lower().replace(" ", "-")
    _line1 = re.sub("[,#.]", "", line1.lower().replace(" ", "-"))

    return f"https://www.aspendental.com/dentist/{_state}/{_city}/{_line1}/"


class AspenDentalUSSpider(JSONBlobSpider):
    name = "aspen_dental_us"
    item_attributes = {
        "brand": "Aspen Dental",
        "brand_wikidata": "Q4807808",
    }
    locations_key = ["data", "facilityCollection", "items"]

    def start_requests(self):
        yield JsonRequest(
            "https://www.aspendental.com/api/bff",
            data={
                "operationName": "bffFacilities",
                "query": QUERY,
                "variables": {"brand": "ASPEN_DENTAL", "take": 10000, "skip": 0},
            },
        )

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["ref"] = location["code"]
        item["street_address"] = merge_address_lines([location["address"]["address1"], location["address"]["address2"]])
        item["extras"]["start_date"] = location["openDate"][:10]
        item["website"] = generate_facility_url(
            location["address"]["stateCode"], location["address"]["city"], location["address"]["address1"]
        )

        oh = OpeningHours()
        for day in location["workingHours"]:
            oh.add_range(day["date"], day["open"]["from"], day["open"]["to"], time_format="%I:%M%p")
        item["opening_hours"] = oh

        yield item
