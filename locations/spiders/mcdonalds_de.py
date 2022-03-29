import re
import scrapy
from locations.items import GeojsonPointItem


class McDonaldsDESpider(scrapy.Spider):
    name = "mcdonalds_de"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["mcdonalds.de"]

    def start_requests(self):
        url = "http://www.mcdonalds.de/search"
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "http://www.mcdonalds.de",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Referer": "http://www.mcdonalds.de/restaurant-suche",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
        }
        form_data = {
            "latitude": "53.0185209",
            "longitude": "6.559760099999949",
            "radius": "1000",
            "searchfield": "99817",
        }

        yield scrapy.http.FormRequest(
            url=url,
            method="POST",
            formdata=form_data,
            headers=headers,
            callback=self.parse,
        )

    def store_hours(self, data):
        day_groups = []
        this_day_group = None
        for day in (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ):
            hour = data[day]
            hour = hour.split("-")

            if len(hour) == 1:
                continue

            day_open = hour[0].strip()
            day_close = hour[1].strip()

            hours = day_open + "-" + day_close
            day_short = day.title()[:2]

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day_short
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)

        day_groups.append(this_day_group)

        if not day_groups:
            return None

        if len(day_groups) == 1:
            if not day_groups[0]:
                return None
            opening_hours = day_groups[0]["hours"]
            if opening_hours == "07:00-07:00":
                opening_hours = "24/7"
        else:
            opening_hours = ""
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        stores = response.json()
        stores = stores["restaurantList"]
        for item in stores:
            store = item["restaurant"]
            properties = {
                "ref": store["id"],
                "name": store["name1"],
                "addr_full": store["street"],
                "city": store["city"],
                "website": store["seoURL"],
                "postcode": store["postalCode"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phone"],
            }

            opening_hours = self.store_hours(store)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
