import json
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS_NAME = {
    'Monday': 'Mo',
    'Tuesday': 'Tu',
    'Wednesday': 'We',
    'Wedsenday': 'We',
    'Thursday': 'Th',
    'Friday': 'Fr',
    'Saturday': 'Sa',
    'Sunday': 'Su'
}

class WellStarSpider(scrapy.Spider):
    name = "wellstar"
    item_attributes = {'brand': "WellStar Health System"}
    allowed_domains = ["www.wellstar.org/"]
    start_urls = ('https://www.wellstar.org/locations',)

    def start_requests(self):
        url = 'https://www.wellstar.org/api/LocationSearchApi/GetLocations'

        headers = {
            "authority": "www.wellstar.org",
            "sec-ch-ua": "\"Chromium\";v=\"88\", \"Google Chrome\";v=\"88\", \";Not A Brand\";v=\"99\"",
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
            "accept-language": "en-US,en;q=0.9"
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
            "_ga": "GA1.1.688932849.1614958557"
        }

        body = '{"searchTerm":"","searchFilter":""}'

        yield scrapy.Request(
            url=url,
            method='POST',
            dont_filter=True,
            cookies=cookies,
            headers=headers,
            body=body,
            callback=self.parse
            )

    def parse_hours(self, hours):

        opening_hours = OpeningHours()

        if hours:
            for dt in hours:
                try:
                    day = DAYS_NAME[dt.split(':')[0]]
                    time = "".join(dt.split(':')[1:4])
                    open_time, close_time = time.split('-')
                    opening_hours.add_range(day=day,
                                            open_time=open_time.strip(),
                                            close_time=close_time.strip(),
                                            time_format="%H%M"
                                            )
                except:
                    continue

        return opening_hours.as_opening_hours()

    def parse(self, response):
        hdata = json.loads(response.text)

        hdata = hdata["SearchResults"]

        for row in hdata:

            properties = {
                'ref': row['LocationID'],
                'name': row['Name'],
                'addr_full': " ".join([row["Address"].split(",")[0], row.get('Address2',"") or ""]).strip(),
                'city': row["Address"].split(",")[1].strip(),
                'state': row["Address"].split(",")[2].strip(),
                'postcode': row["Address"].split(",")[3].strip(),
                'lat': row['Latitude'],
                'lon': row['Longitude'],
                'phone': row['LocationContactPhone']
            }

            hours = self.parse_hours(row['WorkingHours'])
            properties['opening_hours'] = hours

            yield GeojsonPointItem(**properties)
