# -*- coding: utf-8 -*-
import scrapy
import json


from locations.items import GeojsonPointItem

STATES = {
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


class OutbackSteakhouseSpider(scrapy.Spider):
    download_delay = 0.2
    name = "outbacksteakhouse"
    item_attributes = {"brand": "Outback Steakhouse", "brand_wikidata": "Q1064893"}
    allowed_domains = ["outback.com"]
    start_urls = ("https://www.outback.com/partial/subpage_locations_directory",)

    def parse(self, response):
        data = response.xpath("//script[@jsonpush][1]/text()").extract_first()
        coordinates = response.xpath("//script[@jsonpush][2]/text()").extract_first()
        store_data = json.loads(data)
        coordinate_data = json.loads(coordinates)

        for stores_list in store_data:
            stores = stores_list["locations"]
            for store in stores:
                storeid = store["unitId"]
                state = store["state"]
                latlong_data = coordinate_data[0]
                lat = latlong_data[(STATES[state]).upper()]["longLats"][storeid].get(
                    "lat"
                )
                lon = latlong_data[(STATES[state]).upper()]["longLats"][storeid].get(
                    "long"
                )

                properties = {
                    "ref": store["unitId"],
                    "name": store["displayName"],
                    "addr_full": store["address"],
                    "city": store["city"],
                    "state": state,
                    "postcode": store["zip"],
                    "phone": store["phone"],
                    "lat": lat,
                    "lon": lon,
                    "website": "https://www.outback.com" + store["url"],
                }
                yield GeojsonPointItem(**properties)
