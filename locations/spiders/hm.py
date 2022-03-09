import scrapy
from locations.items import GeojsonPointItem
import itertools


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


def partition(l, n):
    return list(chunks(l, n))


def process_hours(opening_hours):
    ret_hours = []
    for hours_str in opening_hours:
        split_hours = (
            hours_str.replace(",", "")
            .replace("AM AM", "")
            .replace("PM PM", "")
            .split(" ")
        )
        if split_hours[1] == "-":
            range_start = split_hours[0]
            range_end = split_hours[2]
            times = partition([x for x in split_hours[3:] if x != "-"], 2)
        else:
            range_start, range_end = split_hours[0], None
            times = partition([x for x in split_hours[1:] if x != "-"], 2)
        periods = partition(times, 2)
        periods = [list(itertools.chain(*r)) for r in periods]

        period_list = []

        for start, start_period, end, end_period in periods:
            start_hour, start_minutes = [int(x) for x in start.split(":")]
            end_hour, end_minutes = [int(x) for x in end.split(":")]

            if start_period == "PM":
                start_hour += 12
            end_hour += 12

            hours = (start_hour, start_minutes, end_hour, end_minutes)
            period_list.append("%02d:%02d-%02d:%02d" % hours)
        periods_str = ", ".join(period_list)
        if range_start and range_end:
            ret_hours.append(
                "{}-{} {}".format(range_start[:2], range_end[:2], periods_str)
            )
        elif range_start:
            ret_hours.append("{} {}".format(range_start[:2], periods_str))
    return "; ".join(ret_hours)


class HMSpider(scrapy.Spider):
    name = "hm-worldwide"
    item_attributes = {"brand": "H&M"}
    all_stores_uri = "https://hm.storelocator.hm.com/rest/storelocator/stores/1.0/locale/en_US/country/{}/"
    start_urls = ["http://www.hm.com/entrance.ahtml"]

    def parse(self, response):
        country_urls = response.css(".column li a::attr('href')").extract()
        country_codes = {x.split("=")[1].split("&")[0].upper() for x in country_urls}
        for country_code in country_codes:
            yield scrapy.Request(
                url=self.all_stores_uri.format(country_code),
                callback=self.parse_country,
            )

    def parse_country(self, response):
        stores = response.css("storeComplete")
        for store in stores:
            point = {
                "lat": store.xpath("latitude/text()").extract_first(),
                "lon": store.xpath("longitude/text()").extract_first(),
                "name": store.xpath("name/text()").extract_first(),
                "addr_full": store.xpath("address/addressLine/text()").extract_first(),
                "city": store.xpath("city/text()").extract_first(),
                "country": store.xpath("country/text()").extract_first(),
                "phone": store.xpath("phone/text()").extract_first(),
                "opening_hours": process_hours(
                    store.xpath("openingHours/openingHour/text()").extract()
                ),
                "ref": store.xpath("storeId/text()").extract_first(),
            }
            if "/country/US" in response.url:
                point["state"] = store.xpath("region/name/text()").extract_first()
                point["postcode"] = (
                    store.xpath("address/addressLine/text()")
                    .extract()[-1]
                    .split(" ")[-1]
                )

            yield GeojsonPointItem(**point)
