# -*- coding: utf-8 -*-
import csv

import scrapy

from locations.items import GeojsonPointItem


class BurgerKingSpider(scrapy.Spider):
    name = "burgerking"
    item_attributes = {"brand": "Burger King", "brand_wikidata": "Q177054"}
    allowed_domains = ["bk.com", "use1-prod-bk.rbictg.com"]
    download_delay = 0.2

    query = "query GetRestaurants($input: RestaurantsInput) {\n  restaurants(input: $input) {\n    pageInfo {\n      hasNextPage\n      endCursor\n      __typename\n    }\n    totalCount\n    nodes {\n      ...RestaurantNodeFragment\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment RestaurantNodeFragment on RestaurantNode {\n  _id\n  storeId\n  isAvailable\n  posVendor\n  chaseMerchantId\n  curbsideHours {\n    ...OperatingHoursFragment\n    __typename\n  }\n  deliveryHours {\n    ...OperatingHoursFragment\n    __typename\n  }\n  diningRoomHours {\n    ...OperatingHoursFragment\n    __typename\n  }\n  distanceInMiles\n  drinkStationType\n  driveThruHours {\n    ...OperatingHoursFragment\n    __typename\n  }\n  driveThruLaneType\n  email\n  environment\n  franchiseGroupId\n  franchiseGroupName\n  frontCounterClosed\n  hasBreakfast\n  hasBurgersForBreakfast\n  hasCatering\n  hasCurbside\n  hasDelivery\n  hasDineIn\n  hasDriveThru\n  hasMobileOrdering\n  hasLateNightMenu\n  hasParking\n  hasPlayground\n  hasTakeOut\n  hasWifi\n  hasLoyalty\n  id\n  isDarkKitchen\n  isFavorite\n  isHalal\n  isRecent\n  latitude\n  longitude\n  mobileOrderingStatus\n  name\n  number\n  parkingType\n  phoneNumber\n  physicalAddress {\n    address1\n    address2\n    city\n    country\n    postalCode\n    stateProvince\n    stateProvinceShort\n    __typename\n  }\n  playgroundType\n  pos {\n    vendor\n    __typename\n  }\n  posRestaurantId\n  restaurantImage {\n    asset {\n      _id\n      metadata {\n        lqip\n        palette {\n          dominant {\n            background\n            foreground\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    crop {\n      top\n      bottom\n      left\n      right\n      __typename\n    }\n    hotspot {\n      height\n      width\n      x\n      y\n      __typename\n    }\n    __typename\n  }\n  restaurantPosData {\n    _id\n    __typename\n  }\n  status\n  vatNumber\n  __typename\n}\n\nfragment OperatingHoursFragment on OperatingHours {\n  friClose\n  friOpen\n  monClose\n  monOpen\n  satClose\n  satOpen\n  sunClose\n  sunOpen\n  thrClose\n  thrOpen\n  tueClose\n  tueOpen\n  wedClose\n  wedOpen\n  __typename\n}\n"

    def make_request(self, lat, lon):
        body = [
            {
                "operationName": "GetRestaurants",
                "variables": {
                    "input": {
                        "filter": "NEARBY",
                        "coordinates": {
                            "userLat": lat,
                            "userLng": lon,
                            "searchRadius": 128000,
                        },
                        "first": 20000,
                        "status": "OPEN",
                    }
                },
                "query": self.query,
            }
        ]
        return scrapy.http.JsonRequest(
            "https://use1-prod-bk.rbictg.com/graphql", data=body
        )

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                yield self.make_request(
                    float(point["latitude"]), float(point["longitude"])
                )

    def parse(self, response):
        data = response.json()
        for row in data[0]["data"]["restaurants"]["nodes"]:
            properties = {
                "ref": row["number"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "name": row["name"],
                "phone": row["phoneNumber"],
                "addr_full": row["physicalAddress"]["address1"],
                "city": row["physicalAddress"]["city"],
                "state": row["physicalAddress"]["stateProvince"],
                "postcode": row["physicalAddress"]["postalCode"],
                "country": row["physicalAddress"]["country"],
                "website": f'https://www.bk.com/store-locator/store/{row["_id"]}',
            }
            yield GeojsonPointItem(**properties)
