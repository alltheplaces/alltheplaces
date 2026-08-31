import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcPHSpider(SitemapSpider):
    name = "kfc_ph"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["www.kfc.com.ph"]
    sitemap_urls = ["https://www.kfc.com.ph/sitemap.xml"]
    sitemap_rules = [(r"/en/store-locator/.+", "parse")]

    def parse(self, response):
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        store = data.get("props", {}).get("pageProps", {}).get("selectedStore", {})
        item = DictParser.parse(store)

        # one non PH location is present at https://www.kfc.com.ph/en/store-locator/kfc_cogeo_antipolo
        # it incorrectly points to Santa Monica, CA, USA
        if item.get("country") == "US":
            return

        address = store.get("address", {})
        item["addr_full"] = address.get("formatted")

        # Santa Monica, CA, USA is present as city in all urls
        item["city"] = None

        if latlng := address.get("latLng"):
            item["lat"], item["lon"] = latlng.get("lat"), latlng.get("lng")

        name_data = item.get("name").get("en_US", "")
        item["name"] = name_data
        item["branch"] = name_data.replace("KFC", "").strip()
        item["website"] = response.url

        raw_hours = store.get("openingHours", [{}])[0].get("en", [])
        all_intervals = [i.lower() for day in raw_hours for i in day]

        if all_intervals and all(i == "open all day" for i in all_intervals):
            item["opening_hours"] = "24/7"

        elif raw_hours:
            oh = OpeningHours()
            for idx, intervals in enumerate(raw_hours):

                # doing this because first OH in the data belongs to Sun whereas first element in DAYS_FULL is Mon
                day_name = DAYS_FULL[(idx - 1) % 7]

                for interval in intervals:
                    low_interval = interval.lower()

                    if "closed" in low_interval:
                        continue
                    elif "open all day" in low_interval:
                        oh.add_range(day_name, "00:00", "23:59")
                    else:
                        oh.add_ranges_from_string(f"{day_name} {interval}")

            item["opening_hours"] = oh

        yield item
