import re
import scrapy
from locations.items import GeojsonPointItem


class McDonaldsITSpider(scrapy.Spider):
    name = "mcdonalds_it"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["mcdonaldsstoreplatform.adattivo.com"]

    def start_requests(self):
        url = "https://mcdonaldsstoreplatform.adattivo.com/v2/sites"
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.mcdonalds.it",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "application/vnd.storeplatform.v2+json",
            "Referer": "https://www.mcdonalds.it/ristorante",
        }

        yield scrapy.http.FormRequest(
            url=url, method="GET", headers=headers, callback=self.parse
        )

    def normalize_time(self, time_str, flag):
        match = re.search(r"([0-9]{1,2}).([0-9]{1,2})", time_str)
        h, m = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if flag and int(h) < 13 else int(h),
            int(m),
        )

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        day_hours = data["days"]
        for day_hour in day_hours:
            hours = ""
            day = day_hour["name"]
            work_time = day_hour["times"]
            if not work_time:
                return None
            start = work_time.split(",")[0].strip()
            end = work_time.split(",")[1].strip()
            start = self.normalize_time(start, False)
            end = self.normalize_time(end, True)
            if day == "Day":
                continue
            short_day = day[:2]
            hours = "{}:{}-{}:{}".format(start[:2], start[3:], end[:2], end[3:])
            if not this_day_group:
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            elif hours == this_day_group["hours"]:
                this_day_group["to_day"] = short_day

            elif hours != this_day_group["hours"]:
                day_groups.append(this_day_group)
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

        day_groups.append(this_day_group)

        if not day_groups:
            return None
        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        results = response.json()
        stores = results["sites"]
        for item in stores:
            properties = {
                "ref": item["id"],
                "name": item["title"],
                "addr_full": item["googlefaddress"],
                "lat": item["geo"]["lat"],
                "lon": item["geo"]["lng"],
                "phone": item["telephone"],
                "city": item["city"],
            }

            opening_hours = self.store_hours(item["opening_hours"][0])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
