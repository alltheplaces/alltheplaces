import datetime
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

day_mapping = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
day_list = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def convert_24hour(time):
    """
    Takes 12 hour time as a string and converts it to 24 hour time.
    """
    time_raw, meridiem = time.split()

    if len(time_raw.split(":")) < 2:
        hour = time_raw
        minute = "00"
    else:
        hour, minute = time_raw.split(":")

    if meridiem.lower() in ["am", "noon"]:
        time_formatted = hour + ":" + minute
        return time_formatted
    elif meridiem.lower() == "pm":
        time_formatted = str(int(time_raw) + 12) + ":" + minute
        return time_formatted


class HalfPriceBooksSpider(scrapy.Spider):
    name = "half_price_books"
    item_attributes = {"brand": "Half Price Books", "brand_wikidata": "Q5641744"}
    allowed_domains = ["hpb.com"]
    start_urls = ("https://www.hpb.com/all-stores-list",)

    def parse(self, response):
        urls = response.xpath('//div[@id="stores-list"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)
        address = response.xpath(
            '//div[@class="font-large font-pn-reg"]/div[1]/text()'
        ).extract_first()
        if address is None:
            return
        address = address.strip()

        properties = {
            "name": response.xpath(
                '//h1[@class="store-details-name"]/text()'
            ).extract_first(),
            "addr_full": address,
            "lat": float(
                response.xpath(
                    '//div[@class="stock_location"]/@data-lat'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//div[@class="stock_location"]/@data-lng'
                ).extract_first()
            ),
            "phone": response.xpath('//div[@class="mts"]/text()').extract_first(),
            "ref": ref,
            "website": response.url,
        }

        hours = self.parse_hours(
            response.xpath('//ul[@class="store-details-hours mts"]/li/text()').extract()
        )

        split_addr = address.split(",")
        if len(split_addr) == 3:
            properties["street_address"] = split_addr[0]
            properties["city"] = split_addr[1].strip()
            properties["state"] = split_addr[2].strip().split(" ")[0]
            properties["postcode"] = split_addr[2].strip().split(" ")[1]
        elif len(split_addr) == 4:
            properties["street_address"] = split_addr[0] + "," + split_addr[1]
            properties["city"] = split_addr[2].strip()
            properties["state"] = split_addr[3].strip().split(" ")[0]
            properties["postcode"] = split_addr[3].strip().split(" ")[1]
        elif len(split_addr) == 2:
            properties["city"] = split_addr[0].strip()
            properties["state"] = split_addr[1].strip()

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        for days in elements:
            if days.split()[0] not in [
                "Mon",
                "Tue",
                "Wed",
                "Thu",
                "Fri",
                "Sat",
                "Sun",
                "Every",
            ]:
                continue
            if len(re.findall(r"(-)", days)) > 1:
                day_start, day_end = [
                    day_mapping[days.split()[0]],
                    day_mapping[days.split()[2]],
                ]

                if day_start > day_end:  # e.g. Sun - Thu
                    day_by_day = day_list[0 : (day_end + 1)]  # take first part of week
                    day_by_day.append(day_list[day_start:7][0])  # append rest of week
                else:
                    day_by_day = day_list[day_start : (day_end + 1)]

                hours = days.split(None, 3)[3]

                for day in day_by_day:
                    open_time = convert_24hour(hours.split("-")[0].strip())
                    close_time = convert_24hour(hours.split("-")[1].strip())
                    opening_hours.add_range(
                        day=day, open_time=open_time, close_time=close_time
                    )
            elif days.split()[0:2] == ["Every", "day"]:
                for day in day_list:
                    hours = days.split(None, 2)[2]
                    open_time = convert_24hour(hours.split("-")[0].strip())
                    close_time = convert_24hour(hours.split("-")[1].strip())
                    opening_hours.add_range(
                        day=day, open_time=open_time, close_time=close_time
                    )
            else:
                day = day_list[day_mapping[days.split()[0]]]
                hours = days.split(None, 1)[1]
                open_time = convert_24hour(hours.split("-")[0].strip())
                close_time = convert_24hour(hours.split("-")[1].strip())
                opening_hours.add_range(
                    day=day, open_time=open_time, close_time=close_time
                )

        return opening_hours.as_opening_hours()
