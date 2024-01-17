import re

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class HolidayStationstoresUSSpider(Spider):
    name = "holiday_stationstores_us"
    item_attributes = {"brand": "Holiday Stationstores", "brand_wikidata": "Q5880490"}
    allowed_domains = ["www.holidaystationstores.com"]

    def start_requests(self):
        yield JsonRequest(
            "https://www.holidaystationstores.com/Locations/GetAllStores",
            method="POST",
            callback=self.parse_all_stores,
        )

    def parse_all_stores(self, response):
        for store_id, store in response.json().items():
            yield Request(
                url=f"https://www.holidaystationstores.com/Locations/Detail?storeNumber={store_id}",
                meta={"store": store},
            )

    def parse(self, response):
        store = response.meta["store"]

        address = response.xpath('//div[@class="col-lg-4 col-sm-12"]/text()')[1].extract().strip()
        city_state = response.xpath('//div[@class="col-lg-4 col-sm-12"]/text()')[2].extract().strip()
        city, state = city_state.split(", ")
        phone = response.xpath('//div[@class="HolidayFontColorRed"]/text()').extract_first().strip()
        services = "|".join(
            response.xpath(
                '//ul[@style="list-style-type: none; padding-left: 1.0em; font-size: 12px;"]/li/text()'
            ).extract()
        ).lower()
        open_24_hours = "24 hours" in response.css(".body-content .col-lg-4").get().lower()

        properties = {
            "lon": store["lng"],
            "lat": store["lat"],
            "street_address": address,
            "phone": phone,
            "ref": store["id"],
            "city": city.strip(),
            "state": state.strip(),
            "website": response.url,
            "opening_hours": "24/7" if open_24_hours else self.opening_hours(response),
        }
        apply_category(Categories.FUEL_STATION, properties)
        apply_yes_no(Fuel.DIESEL, properties, "diesel" in services)
        apply_yes_no(Extras.ATM, properties, "atm" in services)
        apply_yes_no(Fuel.E85, properties, "e85" in services)
        apply_yes_no("hgv", properties, "truck" in services)
        apply_yes_no(Fuel.PROPANE, properties, "propane" in services)
        apply_yes_no(Extras.CAR_WASH, properties, "car wash" in services)
        apply_yes_no(Fuel.CNG, properties, "cng" in services)

        yield Feature(**properties)

    # TODO: clean up opening hours
    def opening_hours(self, response):
        hour_part_elems = response.xpath('//div[@class="row"][@style="font-size: 12px;"]')
        day_groups = []
        this_day_group = None

        if hour_part_elems:
            for hour_part_elem in hour_part_elems:
                day = hour_part_elem.xpath('.//div[@class="col-3"]/text()').extract_first()
                hours = hour_part_elem.xpath('.//div[@class="col-9"]/text()').extract_first()

                if not hours or hours.lower() == "closed":
                    continue

                day = day[:2]
                match = re.search(
                    r"^(\d{1,2}):(\d{2})\s*(a|p)m - (\d{1,2}):(\d{2})\s*(a|p)m?$",
                    hours.lower(),
                )
                (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

                f_hr = int(f_hr)
                if f_ampm == "p":
                    f_hr += 12
                elif f_ampm == "a" and f_hr == 12:
                    f_hr = 0
                t_hr = int(t_hr)
                if t_ampm == "p":
                    t_hr += 12
                elif t_ampm == "a" and t_hr == 12:
                    t_hr = 0

                hours = "{:02d}:{}-{:02d}:{}".format(
                    f_hr,
                    f_min,
                    t_hr,
                    t_min,
                )

                if not this_day_group:
                    this_day_group = {"from_day": day, "to_day": day, "hours": hours}
                elif this_day_group["hours"] != hours:
                    day_groups.append(this_day_group)
                    this_day_group = {"from_day": day, "to_day": day, "hours": hours}
                elif this_day_group["hours"] == hours:
                    this_day_group["to_day"] = day

            if this_day_group:
                day_groups.append(this_day_group)

        hour_part_elems = response.xpath('//span[@style="font-size:90%"]/text()').extract()
        if hour_part_elems:
            day_groups.append({"from_day": "Mo", "to_day": "Su", "hours": "00:00-23:59"})

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours
