import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from locations.hours import DAYS


class CaptainDSpider(scrapy.spiders.SitemapSpider):
    name = "captaind"
    item_attributes = {"brand": "Captain D's", "brand_wikidata": "Q5036616"}
    allowed_domains = ["locations.captainds.com", "api.momentfeed.com"]
    sitemap_urls = ["https://locations.captainds.com/sitemap.xml"]
    sitempa_rules = [("", "parse")]

    def parse(self, response):
        headers = {"Host": "api.momentfeed.com", "Authorization": "AJXCZOENNNXKHAKZ"}
        url = "https://api.momentfeed.com/v1/analytics/api/llp.json?address={}"
        yield scrapy.Request(
            url=url.format(response.url.split("/")[-1].replace("-", "+").replace("_", ".")),
            headers=headers,
            callback=self.parse_store,
        )

    def parse_store(self, response):

        store = response.json()[0].get("store_info")

        oh = OpeningHours()
        for day in store.get("store_hours").split(";")[:-1]:
            info_day = day.split(",")
            oh.add_range(
                day=DAYS[int(info_day[0]) - 1],
                open_time=info_day[1],
                close_time=info_day[2],
                time_format="%H%M",
            )

        props = {
            "name": store.get("brand_name"),
            "ref": store.get("corporate_id"),
            "addr_full": store.get("address"),
            "postcode": store.get("postcode"),
            "state": store.get("region"),
            "website": store.get("website"),
            "city": store.get("locality"),
            "phone": store.get("phone"),
            "lat": float(store.get("latitude")),
            "lon": float(store.get("longitude")),
            "opening_hours": oh.as_opening_hours(),
        }

        yield GeojsonPointItem(**props)
