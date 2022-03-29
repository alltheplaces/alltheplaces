import scrapy
from six.moves.urllib.parse import urlencode
import re
from locations.items import GeojsonPointItem


DAYS = {"1": "Mo", "2": "Tu", "3": "We", "4": "Th", "5": "Fr", "6": "Sa", "7": "Su"}


class JambaJuiceSpider(scrapy.Spider):

    name = "jambajuice"
    item_attributes = {"brand": "Jamba Juice", "brand_wikidata": "Q3088784"}
    allowed_domains = ["https://momentfeed-prod.apigee.net/"]
    download_delay = 1.5
    start_urls = ("https://momentfeed-prod.apigee.net/api/llp.json?",)

    def start_requests(self):

        url = self.start_urls[0]

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.8,ru;q=0.6",
            "Origin": "http://locations.jambajuice.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "http://locations.jambajuice.com/site-map",
            "Connection": "keep-alive",
        }

        params = [("auth_token", "PQUBOCBNLKOUIYUP"), ("sitemap", "true")]
        url = self.start_urls[0] + urlencode(params)

        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse_hours(self, hours):

        if not hours:
            return ""

        days = [x for x in hours.split(";") if x]

        day_hours = {}
        all_days = []
        opening_hours = []
        for day in days:
            matches = re.findall(r"^(.*){1},([\d]{4}),([\d]{4})$", day)

            for day, start, end in matches:
                start_hour_min = "{}:{}".format(start[:2], start[2:])
                end_hour_min = "{}:{}".format(end[:2], end[2:])

                hours = "{}-{}".format(start_hour_min, end_hour_min)
                if not day_hours:
                    day_hours = {
                        "from_day": DAYS[day],
                        "to_day": DAYS[day],
                        "hours": hours,
                    }
                elif hours == day_hours["hours"]:
                    day_hours["to_day"] = DAYS[day]
                elif hours != day_hours["hours"]:
                    all_days.append(day_hours)
                    day_hours = {
                        "from_day": DAYS[day],
                        "to_day": DAYS[day],
                        "hours": hours,
                    }

        for day in all_days:

            osm_hours = ""

            if day["from_day"] == day["to_day"]:
                osm_hours = "{} {}".format(day["from_day"], day["hours"])
            else:
                osm_hours = "{}-{} {}".format(
                    day["from_day"], day["to_day"], day["hours"]
                )

            opening_hours.append(osm_hours)

        return ";".join(opening_hours)

    def parse(self, response):

        stores = response.json()
        for store in stores:
            props = {}
            store_info = store.get("store_info", "")
            props["ref"] = store_info["corporate_id"]
            props["lat"] = store_info["latitude"]
            props["lon"] = store_info["longitude"]
            props["state"] = store_info["region"]
            props["city"] = store_info["locality"]

            props["opening_hours"] = self.parse_hours(store_info.get("store_hours", ""))

            props["addr_full"] = ", ".join(
                [store_info["address"], store_info.get("address_extended", "")]
            )

            sieve_out = ["website", "phone", "postcode", "country"]

            props.update({key: store_info[key] for key in sieve_out})

            yield GeojsonPointItem(**props)
