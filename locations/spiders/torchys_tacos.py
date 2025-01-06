import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class TorchysTacosSpider(scrapy.Spider):
    name = "torchys_tacos"
    item_attributes = {"brand": "Torchy's Tacos", "brand_wikidata": "Q106769573"}
    allowed_domains = ["torchystacos.com"]
    start_urls = ("https://torchystacos.com/locations/",)
    download_delay = 0.7

    def parse(self, response):
        stores = response.xpath('//div[@class="details-title"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(store, callback=self.parse_store)

    def parse_store(self, response):
        store_info = response.xpath('//div[@class="row-wrap store-details"]')
        store_address = response.xpath('.//div[@class="item-details"]/p/a/text()').extract()
        ref = response.xpath("//h1/text()").extract_first()
        store_hours = [d for d in store_info.xpath('.//div[@class="show-more"]/p/@datetime').extract()]

        full_address = [e.strip() for e in store_address[0].split("  ") if e.strip()]
        phone = store_address[1].strip() if len(store_address) > 1 else None
        oh = self.parse_hours(store_hours)

        properties = {
            "addr_full": full_address[0],
            "phone": phone,
            "city": full_address[-3].strip(","),
            "state": full_address[-2],
            "postcode": full_address[-1],
            "ref": ref,
            "website": response.url,
            "lat": store_info.xpath('.//div[@id="ttMap"]/@data-lat').extract_first(),
            "lon": store_info.xpath('.//div[@id="ttMap"]/@data-lon').extract_first(),
            "opening_hours": oh,
        }
        item["street_address"] = item.pop("addr_full", None)
        yield Feature(**properties)

    def parse_hours(self, hours):
        oh = OpeningHours()

        for h in hours:
            # Some days the store is closed
            if "close" in h.lower():
                continue
            d, t = h.split(" ")
            ot, ct = t.split("-")
            days = self.parse_days(d)
            for day in days:
                oh.add_range(day=day, open_time=ot, close_time=ct, time_format="%H:%M")

        return oh.as_opening_hours()

    def parse_days(self, days):
        """Parse day ranges and returns a list of days it represent
        The following formats are considered:
          - Single day, e.g. "Mon", "Monday"
          - Range, e.g. "Mon-Fri", "Tue-Sund", "Sat-Sunday"
          - Two days, e.g. "Sat & Sun", "Friday & Su"

        Returns a list with the weekdays
        """
        # Produce a list of weekdays between two days e.g. su-sa, mo-th, etc.
        if "-" in days:
            d = days.split("-")
            r = [i.strip()[:2] for i in d]
            s = WEEKDAYS.index(r[0].title())
            e = WEEKDAYS.index(r[1].title())
            if s <= e:
                return WEEKDAYS[s : e + 1]
            else:
                return WEEKDAYS[s:] + WEEKDAYS[: e + 1]
        # Two days
        if "&" in days:
            d = days.split("&")
            return [i.strip()[:2].title() for i in d]
        # Single days
        else:
            return [days.strip()[:2].title()]
