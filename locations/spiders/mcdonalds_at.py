import json
import re
import scrapy
from locations.items import GeojsonPointItem

day_formats = {
    "Mon": "Mo",
    "Tues": "Tu",
    "Wed": "We",
    "Thur": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class McDonaldsATSpider(scrapy.Spider):
    name = "mcdonalds_at"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.at"]

    start_urls = ("http://www.mcdonalds.at/restaurant-finder",)

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        weekdays = ["Mo", "Th", "We", "Tu", "Fr", "Sa", "Su"]

        for index, item in enumerate(data):
            if index == 7:
                break

            hours = ""
            day_hour = item.groups()[0]

            if len(day_hour.split("-")) < 2:
                continue

            start = day_hour.split("-")[0].strip()
            end = day_hour.split("-")[1].strip()

            end_hour = end.split(":")[0]
            end_min = end.split(":")[1]

            if int(end_hour) == 0:
                end_hour = "23"
                end_min = "59"

            end = "%02d:%02d" % (
                int(end_hour) + 12 if int(end_hour) < 12 else int(end_hour),
                int(end_min),
            )

            short_day = weekdays[index]
            hours = "{}-{}".format(start, end)
            if not this_day_group:
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            elif hours == this_day_group["hours"]:
                this_day_group["to_day"] = short_day

            elif hours != this_day_group["hours"]:
                day_groups.append(this_day_group)
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

        day_groups.append(this_day_group)

        if not day_groups:
            return None

        if bool(day_groups):
            return None
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
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse_city(self, data):
        data = data.split(" ")
        if len(data) > 1:
            return data[0].strip(), data[1].strip()
        else:
            return data[0].strip(), ""

    def parse_store(self, response):
        address = (
            response.xpath('//div[@class="street"]//text()').extract_first().strip()
        )
        postalCode, city = self.parse_city(
            response.xpath('//div[@class="postal-code-city"]//text()').extract_first()
        )
        phone = response.xpath('//div[@class="field--phone"]//text()').extract_first()
        if phone:
            phone = phone.strip()
        else:
            phone = ""

        properties = {
            "addr_full": address,
            "city": city,
            "name": "McDonald's",
            "postcode": postalCode,
            "phone": phone,
            "ref": response.meta["ref"],
            "lon": response.meta["lon"],
            "lat": response.meta["lat"],
        }

        data = re.finditer(r"<span class=\"label\">.*</span>(.*)</li>", response.text)
        opening_hours = self.store_hours(data)
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        try:
            match = re.search(r"\"markers\":(\[.*\])", response.text)
            data = json.loads(match.groups()[0])
        except ValueError:
            return

        for item in data:
            lat = item["latitude"]
            lon = item["longitude"]
            ref = item["rmt"]

            yield scrapy.Request(
                "http://www.mcdonalds.at/restaurant/overlay/" + ref,
                meta={"lat": lat, "lon": lon, "ref": ref},
                callback=self.parse_store,
            )
