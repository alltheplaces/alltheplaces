import urllib.parse

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


USA_STATES = {
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AS": "American Samoa",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DC": "District of Columbia",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "GU": "Guam",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "PR": "Puerto Rico",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VI": "Virgin Islands",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
}


class DickeysBarbecuePitUSSpider(Spider):
    name = "dickeys_barbecue_pit_us"
    item_attributes = {"brand": "Dickey's Barbecue Pit", "brand_wikidata": "Q19880747"}
    allowed_domains = ["orders-api.dickeys.com"]
    start_urls = ["https://orders-api.dickeys.com/graphql"]

    def start_requests(self):
        graphql_query = """query {
    viewer {
        locationConnection(first: 2000, filter: { isOpened: { eq: true } active: { eq: true } }) {
            edges {
                node {
                    name: label
                    slug
                    ref: storeNumber
                    locationWeekdayConnection(filter: { showHoliday: { eq: true } }) {
                        edges {
                            node {
                                open_time: opened
                                close_time: closed
                                weekday {
                                    day_name: label
                                }
                            }
                        }
                    }
                    address {
                        street_address: address
                        city
                        state {
                            abbreviation
                        }
                        zip
                        latitude
                        longitude
                    }
                    phone {
                        phone
                    }
                    email
                }
            }
        }
    }
}"""
        data = {
            "query": graphql_query
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, data=data, method="POST")

    def parse(self, response):
        for location in response.json()["data"]["viewer"]["locationConnection"]["edges"]:
            location["node"]["address"]["state"] = location["node"]["address"]["state"]["abbreviation"]
            location["node"]["phone"] = location["node"]["phone"]["phone"]
            item = DictParser.parse(location["node"])
            item["lat"] = location["node"]["address"]["latitude"]
            item["lon"] = location["node"]["address"]["longitude"]
            item["website"] = "https://www.dickeys.com/locations/" + USA_STATES[item["state"]].lower() + "/" + urllib.parse.quote(item["city"].lower()) + "/" + location["node"]["slug"]
            item["opening_hours"] = OpeningHours()
            for hours_range in location["node"]["locationWeekdayConnection"]["edges"]:
                if hours_range["node"]["weekday"]["day_name"].title() not in DAYS_FULL:
                    continue
                item["opening_hours"].add_range(hours_range["node"]["weekday"]["day_name"], hours_range["node"]["open_time"], hours_range["node"]["close_time"], "%H:%M:%S")
            yield item
