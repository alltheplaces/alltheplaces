import scrapy
import re
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    "Mon": "Mo",
    "Tues": "Tu",
    "Wed": "We",
    "Thur": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class KoppsSpider(scrapy.Spider):
    name = "kopps"
    item_attributes = {"brand": "Kopp's Frozen Custard", "brand_wikidata": "Q6431150"}
    allowed_domains = ["www.kopps.com"]
    download_delay = 1.5
    start_urls = ("https://www.kopps.com/",)

    def parse_day(self, day):
        if re.search("-", day):
            days = day.split("-")
            osm_days = []
            if len(days) == 2:
                for day in days:
                    if day.strip() in DAY_MAPPING:
                        osm_day = DAY_MAPPING[day.strip()]
                        osm_days.append(osm_day)
            return "-".join(osm_days)

    def parse_times(self, times):
        if times.strip() == "Open 24 hours":
            return "24/7"
        hours_to = [x.strip() for x in times.split("-")]
        cleaned_times = []

        for hour in hours_to:
            if re.search("pm$", hour):
                hour = re.sub("pm", "", hour).strip()
                hour_min = hour.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                cleaned_times.append(":".join(hour_min))

            if re.search("am$", hour):
                hour = re.sub("am", "", hour).strip()
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
            day_times = li.xpath("normalize-space(./text())").extract_first()
            day = re.findall(r"^[a-zA-Z-]+", day_times)
            if len(day) > 0:
                day = day[0]
            else:
                day = "Mon-Sun"
            times = re.findall(
                r"[0-9]{2}:[0-9]{2}[a|p]m - [0-9]{2}:[0-9]{2}[a|p]m", day_times
            )
            times = times[0]
            if times and day:
                parsed_time = self.parse_times(times)
                parsed_day = self.parse_day(day)
                if parsed_day and parsed_time:
                    hours.append(parsed_day + " " + parsed_time)

        return "; ".join(hours)

    def parse(self, response):
        locations = response.xpath('//div[@id="locations"]/div/div')

        for location in locations:
            properties = {
                "addr_full": location.xpath(
                    "normalize-space(./div/address/a/text())"
                ).extract_first(),
                "phone": location.xpath(
                    "normalize-space(./div/ul/li/span/a/text())"
                ).extract_first(),
                "city": location.xpath("./div/address/a/text()")
                .extract()[1]
                .replace(" ", "")
                .split(",")[0]
                .replace("\r\n", ""),
                "state": location.xpath("./div/address/a/text()")
                .extract()[1]
                .lstrip()
                .split(",")[1]
                .split(" ")[1],
                "postcode": location.xpath("./div/address/a/text()")
                .extract()[1]
                .lstrip()
                .split(",")[1]
                .split(" ")[2]
                .replace("\r\n", ""),
                "ref": location.xpath(
                    "normalize-space(./div/address/a/@href)"
                ).extract_first(),
                "website": response.url,
                "lat": re.findall(
                    r"\/[0-9]{2}[^(\/)]+z",
                    location.xpath(
                        "normalize-space(./div/address/a/@href)"
                    ).extract_first(),
                )[0][1:].split(",")[0],
                "lon": re.findall(
                    r"\/[0-9]{2}[^(\/)]+z",
                    location.xpath(
                        "normalize-space(./div/address/a/@href)"
                    ).extract_first(),
                )[0][1:].split(",")[1],
            }

            hours = self.parse_hours(location.xpath("./div/ul/li[3]/span"))
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
