import scrapy
import re
import json
from locations.items import GeojsonPointItem

day_formats = {
    "Mon": "Mo",
    "Tues": "Tu",
    "Wed": "We",
    "Thur": "Th",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class MightytacoSpider(scrapy.Spider):

    name = "mightytaco"
    item_attributes = {"brand": "Mighty Taco"}
    allowed_domains = ["www.mightytaco.com"]
    download_delay = 1.5
    start_urls = ("https://www.mightytaco.com/Locations",)

    def parse_day(self, day):

        if re.search("&", day):
            days = day.split("&")
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = day_formats[day.strip()]
                    osm_days.append(osm_day)
            return osm_days
        if re.search("^Sun$", day):
            return [day_formats["Sun"]]

        if re.search("-", day):
            days = day.split("-")
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = day_formats[day.strip()]
                    osm_days.append(osm_day)
            return ["-".join(osm_days)]

    def parse_times(self, times):
        hours_to = [x.strip() for x in times.split("-")]
        cleaned_times = []
        for hour in hours_to:
            if re.search("Midnight", hour):
                cleaned_times.append("Midnight")
            if re.search("Closed", hour):
                return "Closed"
            if re.search("PM$", hour):
                hour = re.sub("PM", "", hour).strip()
                hour_min = hour.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                cleaned_times.append(":".join(hour_min))

            if re.search("AM$", hour):
                hour = re.sub("AM", "", hour).strip()
                hour_min = hour.split(":")
                if len(hour_min[0]) < 2:
                    hour_min[0] = hour_min[0].zfill(2)
                else:
                    hour_min[0] = str(int(hour_min[0]))

                cleaned_times.append(":".join(hour_min))
        return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day_times = li.replace("\r\n", "").strip()
            day = re.findall(r"\([^(\))]+", day_times)
            if len(day) == 0:
                day = "Mon - Sun"
            else:
                day = day[0][1:]
            times = re.findall(r"^[^\(]+", day_times)
            if times != [] and day:
                parsed_time = self.parse_times(times[0])
                parsed_day = self.parse_day(day)
                if len(parsed_day) == 1:
                    hours.append(parsed_day[0] + " " + parsed_time)
                else:
                    hours.append(parsed_day[0] + " " + parsed_time)
                    hours.append(parsed_day[1] + " " + parsed_time)

        return "; ".join(hours)

    def parse(self, response):
        stores = response.xpath(
            '//div[@class="contentBlocks"]/div[@class="contentBlock animate clear"]/div[@class="float right half copy animate group"]/div'
        )
        map_data = response.xpath("string(//head)").extract_first().strip()
        json_data = re.findall(r"GMap.init\(\{[^()]+json: '[^(')]+", map_data)[
            0
        ].replace(" ", "")[19:]
        location_json = json.loads(json_data)
        data = {}
        for location in location_json["Groups"]:
            for location1 in location["Items"]:
                data[location1["element"]] = {
                    "lat": location1["latitude"],
                    "lon": location1["longitude"],
                }
        for store in stores:
            marker_id = store.xpath("./@id").extract_first()
            properties = {
                "addr_full": store.xpath(
                    'normalize-space(./div/div[@class="address"]/p/text())'
                )
                .extract_first()
                .strip()
                .split(",")[0],
                "phone": store.xpath(
                    'normalize-space(./div/div[@class="gets"]/div[@class="phoneRow clear"]/p/a[@data-show-device="mobile"]/text())'
                ).extract_first(),
                "city": store.xpath(
                    'normalize-space(./div/div[@class="address"]/p/text())'
                )
                .extract_first()
                .strip()
                .split(",")[1],
                "state": store.xpath(
                    'normalize-space(./div/div[@class="address"]/p/text())'
                )
                .extract_first()
                .split(",")[2]
                .lstrip()
                .split(" ")[0],
                "postcode": store.xpath(
                    'normalize-space(./div/div[@class="address"]/p/text())'
                )
                .extract_first()
                .split(",")[2]
                .lstrip()
                .split(" ")[1],
                "ref": response.url,
                "website": response.url,
                "lat": data[marker_id]["lat"],
                "lon": data[marker_id]["lon"],
            }
            hours = self.parse_hours(
                store.xpath(
                    './div/div[@class="hours"]/div[contains(@id  , "DiningRoomHours")]/p[@class="time"]/text()'
                ).extract()
            )
            if hours:
                properties["opening_hours"] = hours
            yield GeojsonPointItem(**properties)
