import json
import scrapy
from locations.items import GeojsonPointItem


STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DC",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]


class KrystalSpider(scrapy.Spider):
    name = "krystal"
    item_attributes = {"brand": "Krystal"}
    allowed_domains = ["krystal.com"]
    download_delay = 1.5
    start_urls = ("http://krystal.com/wp-admin/admin-ajax.php",)
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_hours(self, hours):
        hours = json.loads(hours)
        for key, epoch in hours.items():

            if epoch["open"] == "99":
                epoch["open"] = "00"

            if set(epoch.values()) == set(["99"]):
                hours[key] = "00:00-24:00"
            elif len(epoch["close"]) < 2 and len(epoch["open"]) < 2:
                hours[key] = "0{}:00-0{}:00".format(epoch["open"], epoch["close"])

            elif len(epoch["close"]) < 2 and len(epoch["open"]) >= 2:
                hours[key] = "{}:00-0{}:00".format(epoch["open"], epoch["close"])

            elif len(epoch["open"]) < 2 and len(epoch["close"]) >= 2:
                hours[key] = "0{}:00-{}:00".format(epoch["open"], epoch["close"])

            elif len(epoch["open"]) >= 2 and len(epoch["close"]) >= 2:
                hours[key] = "{}:00-{}:00".format(epoch["open"], epoch["close"])

        reversed_hours = {}
        for key, epoch in hours.items():

            reversed_hours.setdefault(epoch, [])
            reversed_hours[epoch].append(key[:2].title())

        if len(reversed_hours) == 1 and list(reversed_hours)[0] == "00:00-24:00":
            return "24/7"

        opening_hours = []

        for key, value in reversed_hours.items():
            if len(value) == 1:
                opening_hours.append("{} {}".format(value[0], key))
            else:
                opening_hours.append("{}-{} {}".format(value[0], value[-1], key))

        return ";".join(opening_hours)

    def parse(self, response):
        data = response.json()

        for key, store_infor in data.items():
            if isinstance(store_infor, dict):
                opening_hours = self.parse_hours(store_infor["storehours"])

                properties = {
                    "addr_full": store_infor["address"],
                    "phone": store_infor["phone"],
                    "city": store_infor["city"],
                    "state": store_infor["state"],
                    "postcode": store_infor["zip"],
                    "ref": store_infor["unit"],
                    "website": "{}{}{}".format(
                        "http://", self.allowed_domains[0], store_infor["url"]
                    ),
                    "lat": store_infor["lat"],
                    "lon": store_infor["lng"],
                    "opening_hours": opening_hours,
                }
                yield GeojsonPointItem(**properties)

    def start_requests(self):

        headers = {
            "Accept-Language": "en-US,en;q=0.8,ru;q=0.6",
            "Origin": "http://krystal.com",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Referer": "http://krystal.com/locations/",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
        }

        for state in STATES:
            form_data = {
                "action": "get_locations_set_by_state",
                "data[devicelng]": "-77.2888",
                "data[maplng]": "-86.8073",
                "data[maplat]": "32.799",
                "data[devicelat]": "38.8318",
                "data[state]": state,
                "data[numresults]": "10",
            }

            yield scrapy.http.FormRequest(
                url=self.start_urls[0],
                method="POST",
                formdata=form_data,
                headers=headers,
                callback=self.parse,
            )
