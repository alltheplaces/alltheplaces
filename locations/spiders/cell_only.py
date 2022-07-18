import re
import scrapy
from locations.items import GeojsonPointItem

# zips = ['57104', '50001', '55090', '63017', '68001', '66101', '53001']
zips = [
    {"zip": "57104", "lat": "43.6032799", "lng": "-96.71729069999998"},
    {"zip": "50001", "lat": "41.3596647", "lng": "-93.44983460000003"},
    {"zip": "66101", "lat": "39.11738830000001", "lng": "-94.62695719999999"},
    {"zip": "63017", "lat": "38.6633659", "lng": "-90.57714929999997"},
    {"zip": "53001", "lat": "43.6021055", "lng": "-88.07053189999999"},
    {"zip": "68001", "lat": "41.334669", "lng": "-96.95110899999997"},
    {"zip": "55111", "lat": "44.8849345", "lng": "-93.21312319999998"},
    {"zip": "50047", "lat": "41.4500127", "lng": "-93.4397386"},
    # {'zip': '', 'lat': '', 'lng': ''},
]


def normalize_dayrange(dayrange):
    replacements = [
        ["MON", "Mo"],
        ["TUE", "Tu"],
        ["WED", "We"],
        ["THU", "Th"],
        ["FRI", "Fr"],
        ["SAT", "Sa"],
        ["SUN", "Su"],
    ]
    for r in replacements:
        dayrange = dayrange.replace(r[0], r[1])
    return dayrange


class CellOnlySpider(scrapy.Spider):
    name = "cellonly"
    item_attributes = {"brand": "CellOnly"}
    allowed_domains = ["cell-only.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def process_hours(self, hours):
        if not hours:
            return None
        output = ""
        hours = hours[7:].strip()
        parts = re.findall(r"[A-Z\-]+\: (?:[0-9]+\-[0-9]+|Closed)", hours)
        for part in parts:
            dayrange, hours = part.split(": ")
            if "Closed" in hours:
                continue
            dayrange = normalize_dayrange(dayrange)
            start, end = hours.split("-")
            start = int(start)
            end = int(end)
            start = "%02d:00" % (start)
            end = "%02d:00" % (end + 12)
            output += dayrange + " " + start + "-" + end + ";"
        return output

    def start_requests(self):
        url = "https://cell-only.com/wp-admin/admin-ajax.php"
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.cell-only.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Referer": "https://www.cell-only.com/locations/",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }
        for zipcode in zips:
            form_data = {
                "formdata": "addressInput=%s" % zipcode["zip"],
                "address": zipcode["zip"],
                "lat": zipcode["lat"],
                "lng": zipcode["lng"],
                "options[initial_radius]": "25000",
                "options[ignore_radius]": "0",
                "options[immediately_show_locations]": "0",
                "radius": "25000",
                "action": "csl_ajax_search",
            }
            yield scrapy.http.FormRequest(
                url=url,
                method="POST",
                formdata=form_data,
                headers=headers,
                callback=self.parse,
            )

    def parse(self, response):
        data = response.json()
        stores = data["response"]
        for store in stores:
            properties = {
                "ref": store["id"],
                "name": store["name"],
                "addr_full": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "lat": store["lat"],
                "lon": store["lng"],
                "opening_hours": self.process_hours(store["hours"]),
            }

            phone = store["phone"].replace("\t", "")
            properties["phone"] = phone

            yield GeojsonPointItem(**properties)
