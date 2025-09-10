import json
import re

import scrapy

from locations.items import Feature

DAY_MAPPING = {"Lunes": "Mo", "Sábados": "Sa", "Domingos": "Su"}


class LagenovesaSpider(scrapy.Spider):
    name = "lagenovesa"
    item_attributes = {"brand": "La Genovesa"}
    custom_settings = {"DOWNLOAD_DELAY": 1.5}
    allowed_domains = ["lagenovesasuper.com.ar"]
    start_urls = ("http://lagenovesasuper.com.ar/index.php/empresa/sucursales",)

    def parse_day(self, day):
        if re.search("Domingos", day):
            return DAY_MAPPING[day.strip()]
        if re.search(" a ", day):
            days = day.split(" a ")
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = DAY_MAPPING[day.strip()]
                    osm_days.append(osm_day)
            return "-".join(osm_days)

    def parse_times(self, times):
        cleaned_times = []
        for hours in times.split(" y"):
            hours_to = [x.strip() for x in hours.split(" a ")]
            for hour in hours_to:
                hour = re.sub(r"hs(.|)", "", hour).strip()
                if re.search(":", hour):
                    hour_min = hour.split(":")
                    if int(hour_min[0]) < 10:
                        hour_min[0] = hour_min[0].zfill(2)
                    cleaned_times.append(":".join(hour_min))

                else:
                    if int(hour) < 10:
                        hour = hour.zfill(2)
                    cleaned_times.append(hour + ":00")
            return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.split(" de ")[0]
            times = li.split(" de ")[1]
            if times and day:
                parsed_time = self.parse_times(times)
                parsed_day = self.parse_day(day)
                hours.append(parsed_day + " " + parsed_time)

        return "; ".join(hours)

    def parse_phone(self, str):
        phones = str.replace(" ", "").split("/")
        str_phone = ""
        for phone in phones:
            if len(phone.strip()) < 5:
                str_phone = str_phone + phones[0][:5].strip() + phone.strip() + " "
            else:
                str_phone = str_phone + phone.strip() + " "
        return str_phone

    def parse(self, response):
        stores = response.xpath(
            '//div[@class="uk-width-medium-1-2"]/div[@class="uk-panel uk-panel-box"]|//div[@class="uk-width-medium-1-3"]/div[@class="uk-panel uk-panel-box"]'
        )
        map_data = response.xpath(
            'normalize-space(//div[@class="wk-map wk-map-default"]/@data-options)'
        ).extract_first()
        map_json = json.loads(map_data)

        for idx, store in enumerate(stores):
            lat = ""
            lng = ""
            title = store.xpath("string(./h4)").extract_first()
            for address in map_json["adresses"]:
                if address["title"] == title:
                    lat = float(address["lat"])
                    lng = float(address["lng"])
                    break

            addr_full_phone = store.xpath("string(./p[1])").extract_first()
            addr_full_phone_split = addr_full_phone.split("Teléfonos:")
            if len(addr_full_phone_split) == 1:
                addr_full_phone_split = addr_full_phone.split("Teléfono:")
            addr_full = addr_full_phone_split[0]
            phone = self.parse_phone(addr_full_phone_split[1])

            properties = {
                "addr_full": addr_full,
                "phone": phone,
                "city": "",
                "state": "",
                "postcode": "",
                "ref": title,
                "website": response.url,
                "lat": lat,
                "lon": lng,
            }
            hours = self.parse_hours(store.xpath("./p[2]/text()").extract())
            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
