from copy import deepcopy

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class SpecsaversSpider(Spider):
    name = "specsavers"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    allowed_domains = [
        "www.specsavers.co.uk",
        "www.specsavers.ca",
        "www.specsavers.com.au",
    ]

    def start_requests(self):
        for domain in self.allowed_domains:
            country_code = domain[-2:].upper()
            if country_code == "UK":
                country_code = "GB"
            url = f"https://{domain}/graphql"
            graphql_query = """query storeSearchQuery($query: StoresGeographicSearch!, $limit: Int = 10000, $offset: Int = 0) {
    storesSearch(query: $query, limit: $limit, offset: $offset) {
        count
        offset
        total
        stores {
            distance
            store {
                id
                name
                shortName
                address { ...address }
                coordinates {
                    longitude
                    latitude
                }
                accessibility {
                    description
                    accessibility
                    parkingAvailable
                    parkingDescription
                }
                url
                timeZone
                contactInfo { ...storeContactInfo }
                optical {
                    id
                    storeNumber
                    contactInfo { ...storeContactInfo }
                    enabledForOnlineBooking
                    onlineAppointmentTypes
                    winkAdditionalFields {
                    winkId
                    winkName
                    winkStoreId
                    }
                }
                audiology {
                    id
                    storeNumber
                    contactInfo { ...storeContactInfo }
                    enabledForOnlineBooking
                    onlineAppointmentTypes
                }
                sectionalNotification { ...sectionalNotification }
            }
        }
    }
}
fragment address on Address {
    id
    name
    line1
    line2
    line3
    postcode
    city
    region
    countryCode
    country
}
fragment storeContactInfo on ContactInfo {
    email
    phone
}
fragment sectionalNotification on StoreSectionalNotification {
    title
    headline
    important
    type
    moreInfoLink
    phoneNumber
    includeBookingJourney
    expiryDate
    activeInactive
}"""
            data = {
                "operationName": "storeSearchQuery",
                "query": graphql_query,
                "variables": {
                    "limit": 10000,
                    "offset": 0,
                    "query": {
                        "countryCode": country_code,
                        "latitude": 0,
                        "longitude": 0,
                        "radiusInKm": 100000,
                    },
                },
            }
            yield JsonRequest(url=url, data=data, method="POST")

    def parse(self, response):
        for location in response.json()["data"]["storesSearch"]["stores"]:
            store = location["store"]
            base_item = DictParser.parse(store)
            base_item["street_address"] = clean_address(
                [store["address"].get("line1"), store["address"].get("line2"), store["address"].get("line3")]
            )
            if base_item["state"] == "GGY":
                base_item["country"] = "GG"
            elif base_item["state"] == "JSY":
                base_item["country"] = "JE"
            elif base_item["state"] == "IMN":
                base_item["country"] = "IM"
            if (
                store.get("optical")
                and store.get("audiology")
                and store["optical"]["storeNumber"] == store["audiology"]["storeNumber"]
            ):
                store["optical"]["storeNumber"] = store["optical"]["storeNumber"] + "_O"
                store["audiology"]["storeNumber"] = store["audiology"]["storeNumber"] + "_A"
            for store_type in ["optical", "audiology"]:
                if not store.get(store_type):
                    continue
                item = deepcopy(base_item)
                item["ref"] = store[store_type]["storeNumber"]
                if store[store_type].get("contactInfo"):
                    item["phone"] = store[store_type]["contactInfo"].get("phone")
                    item["email"] = store[store_type]["contactInfo"].get("email")
                if store_type == "optical":
                    apply_category(Categories.SHOP_OPTICIAN, item)
                    item["extras"]["healthcare"] = "optometrist"
                elif store_type == "audiology":
                    apply_category(Categories.SHOP_HEARING_AIDS, item)
                    item["extras"]["healthcare"] = "audiologist"
                yield item
