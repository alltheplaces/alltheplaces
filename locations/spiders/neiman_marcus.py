import scrapy
import re
from locations.items import GeojsonPointItem


class NeimanMarcusSpider(scrapy.Spider):

    name = "neiman_marcus"
    item_attributes = {"brand": "Neiman Marcus"}
    allowed_domains = ["www.neimanmarcus.com"]
    start_urls = ("http://www.neimanmarcus.com/en-au/stores/locations",)

    def parse_day(self, day):
        if re.search("-", day):
            days = day.split("-")
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = day.strip()[:2]
                    osm_days.append(osm_day)
            return "-".join(osm_days)
        return day.strip()[:2]

    def parse_times(self, times):
        if times.strip() == "CLOSED":
            return "Closed"
        hours_to = [x.strip() for x in times.split("-")]
        cleaned_times = []

        for hour in hours_to:
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
            day = li.xpath("normalize-space(./td[1]/text())").extract_first()
            times = li.xpath("normalize-space(./td[2]/text())").extract_first()
            if times and day:
                parsed_time = self.parse_times(times[1:])
                parsed_day = self.parse_day(day)
                hours.append(parsed_day + " " + parsed_time)

        return "; ".join(hours)

    def parse(self, response):
        stores = response.xpath('//div[@class="store-info nmResult-store-info"]')
        for idx, store in enumerate(stores):
            location = re.findall(
                r"sll=[^&]+",
                store.xpath(
                    'normalize-space(./div[@class="grid-60 tablet-grid-50 grid-parent directory"]/span/div[@class="map-directions"]/a/@onclick)'
                ).extract_first(),
            )
            if len(location) > 0:
                lat = float(location[0][4:].split(",")[0])
                lng = float(location[0][4:].split(",")[1])
            else:
                lat = ""
                lng = ""
            properties = {
                "addr_full": store.xpath(
                    'normalize-space(./div[@class="grid-60 tablet-grid-50 grid-parent directory"]/span/p/span[@itemprop="streetAddress"]/text())'
                ).extract_first(),
                "phone": store.xpath(
                    'normalize-space(./div[@class="grid-60 tablet-grid-50 grid-parent directory"]/span/div[@class="hide-on-mobile"]/span[@itemprop="telephone"]/a/text())'
                ).extract_first(),
                "city": store.xpath(
                    'normalize-space(./div[@class="grid-60 tablet-grid-50 grid-parent directory"]/span/p/span[@itemprop="addressLocality"]/text())'
                )
                .extract_first()
                .replace(",", ""),
                "state": store.xpath(
                    'normalize-space(./div[@class="grid-60 tablet-grid-50 grid-parent directory"]/span/p/span[@itemprop="addressRegion"]/text())'
                ).extract_first(),
                "postcode": store.xpath(
                    'normalize-space(./div[@class="grid-60 tablet-grid-50 grid-parent directory"]/span/p/span[@itemprop="postalCode"]/text())'
                ).extract_first(),
                "ref": idx,
                "website": response.url,
                "lat": lat,
                "lon": lng,
            }
            hours = self.parse_hours(
                store.xpath(
                    './div[@class="grid-40 tablet-grid-50 grid-parent store-hours directory"]/table/tr'
                )
            )
            if hours:
                properties["opening_hours"] = hours
            yield GeojsonPointItem(**properties)
