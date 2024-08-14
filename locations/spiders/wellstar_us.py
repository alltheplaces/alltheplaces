import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

DAYS_NAME = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Wedsenday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}

CATEGORY_MAP = {
    "Community Hospice": Categories.HOSPICE,
    "Diabetes Center": Categories.CLINIC,
    "Emergency Department": Categories.EMERGENCY_WARD,
    "Health Park": Categories.HOSPITAL,
    "Hospital": Categories.HOSPITAL,
    "Imaging Center": Categories.CLINIC,
    "Lab Services": Categories.MEDICAL_LABORATORY,
    "Medical Practice": Categories.DOCTOR_GP,
    "Pharmacy": Categories.PHARMACY,
    "Rehabilitation Center": Categories.REHABILITATION,
    "Senior Living": Categories.NURSING_HOME,
    "Urgent Care": Categories.CLINIC_URGENT,
    "Infusion Center": Categories.CLINIC,
}


class WellstarUSSpider(scrapy.Spider):
    name = "wellstar_us"
    item_attributes = {"brand": "WellStar Health System", "brand_wikidata": "Q7981073"}
    allowed_domains = ["www.wellstar.org"]
    start_urls = ("https://www.wellstar.org/locations",)
    requires_proxy = "US"  # Cloudflare geoblocking in use

    def start_requests(self):
        url = "https://www.wellstar.org/api/LocationSearchApi/GetLocations"

        headers = {
            "authority": "www.wellstar.org",
            "sec-ch-ua": '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
            "accept": "application/json, text/javascript, */*; q=0.01",
            "sec-ch-ua-mobile": "?0",
            "__requestverificationtoken": "Y0cuJinQRzvtT-kjKKyPZOlZPu0JU48XSyIvEl1p__yzZF4621s-0YUAkImeXkjGgLB7GyZlv8rYby0uII9LChhFlrKiWiDb2Va5skX-TmM1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
            "content-type": "application/json",
            "origin": "https://www.wellstar.org",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.wellstar.org/locations",
            "accept-language": "en-US,en;q=0.9",
        }

        cookies = {
            "ASP.NET_SessionId": "24p11pgzrg42p4ghtqwi40gl",
            "__RequestVerificationToken": "3agF8JY4gLGMg_K1j7eXWtME4IsQmLPf1snFPF0d132SBNJG2JsIHpVgCAJ1cVysztrjgXuRrCmeMYp9kJjHDYNZlqIzc_ZYwq-TmGIeBTk1",
            "sxa_site": "WellStarOrg",
            "ARRAffinity": "e29b803b013c7e5c76a254365bc4ef36ddc3a862faece1b8869fa46de635b9c5",
            "ARRAffinitySameSite": "e29b803b013c7e5c76a254365bc4ef36ddc3a862faece1b8869fa46de635b9c5",
            "_gid": "GA1.2.1358908497.1614958557",
            "_fbp": "fb.1.1614958557337.1409275872",
            "_gcl_au": "1.1.1318529675.1614958557",
            "SC_ANALYTICS_GLOBAL_COOKIE": "da85aa2fb9ad429eb899c581fcb2376d|True",
            "fs_uid": "rs.fullstory.com#10J51H#5729266957271040:6498357093580800/1646494557",
            "isIUnderstand": "true",
            "searchedlatitude": "33.7489954",
            "searchedlongitude": "-84.3879824",
            "latitude": "30.259263699999998",
            "longitude": "-97.7393472",
            "_gat_UA-9373927-15": "1",
            "_gat_UA-9373927-14": "1",
            "_ga_BM192ND27H": "GS1.1.1614983138.7.1.1614983410.0",
            "_ga": "GA1.1.688932849.1614958557",
        }

        body = '{"searchTerm":"","searchFilter":""}'

        yield scrapy.Request(
            url=url,
            method="POST",
            dont_filter=True,
            cookies=cookies,
            headers=headers,
            body=body,
            callback=self.parse,
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        if hours:
            for dt in hours:
                try:
                    day = DAYS_NAME[dt.split(":")[0]]
                    open_time, close_time = hours.get(dt).split("-")
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time.replace(":", "").strip(),
                        close_time=close_time.replace(":", "").strip(),
                        time_format="%H%M",
                    )
                except Exception:
                    continue

        return opening_hours.as_opening_hours()

    def get_address_attributes(self, address):
        address_parts = address.split(",")
        address_attributes = {}
        if len(address_parts) > 1:
            address_attributes["city"] = address_parts[1].strip()
        if len(address_parts) > 2:
            address_attributes["state"] = address_parts[2].strip()
        if len(address_parts) > 3:
            address_attributes["postcode"] = address_parts[3].strip()

        return address_attributes

    def parse(self, response):
        hdata = json.loads(response.text)

        hdata = hdata["matchingItems"]

        for row in hdata:
            address_data = row.pop("Address")
            address_attributes = self.get_address_attributes(address_data)
            item = DictParser.parse(row)
            item["ref"] = row.get("LocationID")
            item["phone"] = row.get("LocationContactPhone")
            item["addr_full"] = " ".join([address_data.split(",")[0], row.get("Address2", "") or ""]).strip()
            item["city"] = address_attributes.get("city")
            item["state"] = address_attributes.get("state")
            item["postcode"] = address_attributes.get("postcode")
            item["website"] = "https://www.wellstar.org" + row["PageURL"]
            hours = self.parse_hours(row.get("Hours"))
            item["opening_hours"] = hours

            if cat := CATEGORY_MAP.get(row["LocationTypes"][0]):
                apply_category(cat, item)

            yield item
