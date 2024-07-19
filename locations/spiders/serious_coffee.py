import re

import scrapy

from locations.categories import Categories
from locations.items import Feature


class SeriousCoffeeSpider(scrapy.Spider):
    name = "serious_coffee"
    item_attributes = {"brand": "Serious Coffee", "extras": Categories.COFFEE_SHOP.value}
    allowed_domains = ["www.seriouscoffee.com"]
    start_urls = ("http://www.seriouscoffee.com/locations/",)

    def parse_day(self, day):
        if re.search("-", day):
            days = day.split("-")
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = day.strip()[:2]
                    osm_days.append(osm_day)
            return "-".join(osm_days)
        if re.search("Every Day", day):
            return "Mo-Su"
        return day.strip()[:2]

    def parse_times(self, times):
        if times.strip() == "Closed":
            return "Closed"
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
            day = li.xpath('normalize-space(.//td[@class="locations_timetable_day"]/text())').extract_first()
            times = li.xpath('normalize-space(.//td[@class="locations_timetable_time"]/text())').extract_first()
            if times and day:
                parsed_time = self.parse_times(times)
                parsed_day = self.parse_day(day)
                hours.append(parsed_day + " " + parsed_time)

        return "; ".join(hours)

    def parse_stores(self, response):
        address_list = response.xpath(
            '//div[@class="cms_locations_mapaddress"]/div[@class="cms_locations_addressphone"]/div[@class="location_address"]/text()'
        ).extract()
        if len(address_list) > 2:
            address_full = "".join(x for x in address_list[0:2])
        else:
            address_full = address_list[0]
        if len(address_list) > 2:
            city = address_list[2].split(",")[0].strip()
        else:
            city = address_list[1].split(",")[0].strip()
        if len(address_list) > 2:
            state = address_list[2].split(",")[1].lstrip().split(" ")[0].strip()
        else:
            state = address_list[1].split(",")[1].lstrip().split(" ")[0].strip()
        if len(address_list) > 2:
            postcode = (
                address_list[2].split(",")[1].lstrip().split(" ")[2].strip()
                + " "
                + address_list[2].split(",")[1].lstrip().split(" ")[3].strip()
            )
        else:
            postcode = (
                address_list[1].split(",")[1].lstrip().split(" ")[2].strip()
                + " "
                + address_list[1].split(",")[1].lstrip().split(" ")[3].strip()
            )
        page_content = response.text
        latitude = re.findall("var latitude = [^(;)]+", page_content)
        if len(latitude) > 0:
            latitude = float(latitude[0][15:])
        else:
            latitude = ""
        longitude = re.findall("var longitude  = [^(;)]+", page_content)
        if len(longitude) > 0:
            longitude = float(longitude[0][17:])
        else:
            longitude = ""
        properties = {
            "addr_full": address_full,
            "phone": response.xpath(
                'normalize-space(//div[@class="cms_locations_mapaddress"]/div[@class="cms_locations_addressphone"]/div[@class="location_contact"]/text())'
            )
            .extract_first()
            .replace("\xa0 ", ""),
            "city": city,
            "state": state,
            "postcode": postcode,
            "ref": re.findall(r"com\/[^(\/)]+", response.url)[0][4:],
            "website": response.url,
            "lat": latitude,
            "lon": longitude,
        }
        hours = self.parse_hours(response.xpath('//table[@class="locations_timetable_table"]/tr'))
        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath(
            '//div[@class="cms_ldirectory_item"]/div[@class="cms_ldirectory_image"]/a/@href'
        ).extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="cms_locations_main"]/div[@class="cms_locations_image"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
