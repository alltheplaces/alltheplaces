# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class KingSooperSpider(scrapy.Spider):
    name = "king_sooper"
    item_attributes = {"brand": "King Sooper"}
    allowed_domains = ["www.kingsoopers.com"]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0",
    }
    start_urls = (
        "https://www.kingsoopers.com/stores?address=37.7578595,-79.76804&includeThirdPartyFuel=true&maxResults=50&radius=3000&showAllStores=false&useLatLong=true",
    )

    download_delay = 0.5

    store_types = {
        "": "unknown-blank",
        "C": "grocery",
        "F": "unknown-f",
        "G": "gas station",
        "I": "unknown-i",
        "J": "unknown-j",
        "M": "grocery",
        "Q": "unknown-q",
        "S": "grocery",
        "X": "unknown-x",
    }

    ll_requests = set()

    def start_requests(self):

        url = self.start_urls[0]

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br",
        }

        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def store_hours(self, store_hours):
        if all([h == "" for h in store_hours.values()]):
            return None
        else:
            day_groups = []
            this_day_group = None
            for day in (
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ):
                day_open = store_hours[day + "Open"]
                day_close = store_hours[day + "Close"]
                hours = day_open + "-" + day_close
                day_short = day.title()[:2]

                if not this_day_group:
                    this_day_group = dict(
                        from_day=day_short, to_day=day_short, hours=hours
                    )
                elif this_day_group["hours"] == hours:
                    this_day_group["to_day"] = day_short
                elif this_day_group["hours"] != hours:
                    day_groups.append(this_day_group)
                    this_day_group = dict(
                        from_day=day_short, to_day=day_short, hours=hours
                    )
            day_groups.append(this_day_group)

            if len(day_groups) == 1:
                opening_hours = day_groups[0]["hours"]
                if opening_hours == "07:00-07:00":
                    opening_hours = "24/7"
            else:
                opening_hours = ""
                for day_group in day_groups:
                    if day_group["from_day"] == day_group["to_day"]:
                        opening_hours += "{from_day} {hours}; ".format(**day_group)
                    else:
                        opening_hours += "{from_day}-{to_day} {hours}; ".format(
                            **day_group
                        )
                opening_hours = opening_hours[:-2]

            return opening_hours

    def phone_number(self, phone):
        return "{}-{}-{}".format(phone[0:3], phone[3:6], phone[6:10])

    def address(self, address):
        if not address:
            return None

        (num, rest) = address["addressLineOne"].split(" ", 1)
        addr_tags = {
            "housenumber": num.strip(),
            "street": rest.strip(),
            "city": address["city"],
            "state": address["state"],
            "postcode": address["zipCode"],
        }

        return addr_tags

    def parse(self, response):
        data = response.json()

        bounding_box = {
            "min_lat": 100,
            "max_lat": -100,
            "min_lon": 300,
            "max_lon": -300,
        }

        for store in data:
            store_information = store["storeInformation"]
            store_hours = store["storeHours"]

            properties = {
                "phone": self.phone_number(store_information["phoneNumber"]),
                "ref": store_information["recordId"],
                "name": store_information["localName"],
                "type": self.store_types[store_information["storeType"]],
                "opening_hours": self.store_hours(store_hours),
            }

            address = self.address(store_information["address"])
            if address:
                properties.update(address)

            lon_lat = [
                float(store_information["latLong"]["longitude"]),
                float(store_information["latLong"]["latitude"]),
            ]

            bounding_box["min_lat"] = min(bounding_box["min_lat"], lon_lat[1])
            bounding_box["max_lat"] = max(bounding_box["max_lat"], lon_lat[1])
            bounding_box["min_lon"] = min(bounding_box["min_lon"], lon_lat[0])
            bounding_box["max_lon"] = max(bounding_box["max_lon"], lon_lat[0])

            yield GeojsonPointItem(**properties)

        if data:
            box_corners = [
                "{},{}".format(bounding_box["min_lat"], bounding_box["min_lon"]),
                "{},{}".format(bounding_box["max_lat"], bounding_box["min_lon"]),
                "{},{}".format(bounding_box["min_lat"], bounding_box["max_lon"]),
                "{},{}".format(bounding_box["max_lat"], bounding_box["max_lon"]),
            ]

            for corner in box_corners:
                if corner in self.ll_requests:
                    self.logger.info(
                        "Skipping request for %s because we already did it", corner
                    )
                else:
                    self.ll_requests.add(corner)
                    yield scrapy.Request(
                        "https://www.kingsoopers.com/stores?address={}&includeThirdPartyFuel=true&maxResults=50&radius=3000&showAllStores=false&useLatLong=true".format(
                            corner
                        ),
                    )
        else:
            self.logger.info("No results")
