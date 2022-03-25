import json
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}

COOKIES = {
    "bm_sz": "04B124C1C96D68082A9F61BAAAF0B6D5~YAAQdjsvF22E8Xl6AQAACr1VfAxPEt+enarZyrOZrBaNvyuX71lK5QPuDR/FgDEWBZVMRhjiIf000W7Z1PiAjxobrz2Y5LcYMH3CvUNvpdS3MjVLUMGwMEBCf9L5nD5Gs9ho2YL8T7Tz7lYvpolvaOlJnKrHyhCFxxk/uyBZ2G/0QrGKLwSaCQShDsz7ink=",
    "_abck": "440E40C406E69413DCCC08ABAA3E9022~-1~YAAQdjsvF26E8Xl6AQAACr1VfAYznoJdJhX7TNIZW1Rfh6qRhzquXg+L1TWoaL7nZUjXlNls2iPIKFQrCdrWqY/CNXW+mHyXibInMflIXJi5VVB/Swq53kABYJDuXYSlCunYvJAzMSr1q12NOYswz134Y8HRNzVWhkb2jMS5whmHxS/v0vniIvS1TQtKjEQlMGzQYmN41CmLX0JobipQhDtUB4VyNwztb2DCAZiqDX8BLwWg7h/DtPd4158qU69hNhayFTgWmD76/MiR8/T536tMmcoRyWLl4fEtP/XUmKOcksuZO7dbfNxXBffTxIXPYwf1eO77LNuZTCQq5kfsGZLJX8ODju2KSjnIF1vdnyHAe98FDIm+hw==~-1~-1~-1",
}

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "cache-control": "max-age=0",
    "referer": "https://www.tesco.com/store-locator/?q=london&qp=london&l=en",
    "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    "sec-ch-ua-mobile": "?0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36",
}


class TescoSpider(scrapy.Spider):
    name = "tesco"
    item_attributes = {"brand": "Tesco"}
    allowed_domains = ["www.tesco.com"]
    download_delay = 0.3
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    }

    def store_hours(self, store_hours):
        opening_hours = OpeningHours()
        store_hours = json.loads(store_hours)

        for day in store_hours:
            closed = day["isClosed"]
            if not closed:
                opening_hours.add_range(
                    day=DAY_MAPPING[day["day"]],
                    open_time=str(day["intervals"][0]["start"]).zfill(4),
                    close_time=str(day["intervals"][0]["end"]).zfill(4),
                    time_format="%H%M",
                )

        return opening_hours.as_opening_hours()

    def start_requests(self):
        url = "https://www.tesco.com/store-locator/sitemap.xml"

        yield scrapy.http.FormRequest(
            url=url,
            method="GET",
            dont_filter=True,
            cookies=COOKIES,
            headers=HEADERS,
            callback=self.parse,
        )

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()

        # Exclude location subpages for at-store services
        service_paths = [
            "petrol-filling-station",
            "cafe",
            "travel-money",
            "f-f-clothing",
            "pharmacy",
        ]

        for url in urls:
            if not any(service_path in url for service_path in service_paths):

                yield scrapy.http.FormRequest(
                    url=url,
                    method="GET",
                    dont_filter=True,
                    cookies=COOKIES,
                    headers=HEADERS,
                    callback=self.parse_store,
                )

    def parse_store(self, response):
        city_page = response.xpath(
            '//span[@class="Hero-title Hero-title--top"]/text()'
        ).extract_first()

        if not city_page:  # and is a store page
            store_details = response.xpath(
                '//script[@type="application/json" and contains(text(),"storeID")]/text()'
            ).extract_first()
            if store_details:
                store_data = json.loads(store_details)
                ref = store_data["storeID"]
                name = store_data["pageName"]
                addr_1 = response.xpath(
                    '//div[@class="Core-infoWrapper"]//span[@class="Address-field Address-line1"]/text()'
                ).extract_first()
                addr_2 = response.xpath(
                    '//div[@class="Core-infoWrapper"]//span[@class="Address-field Address-line2"]/text()'
                ).extract_first()
                if addr_2:
                    addr_full = ", ".join([addr_1.strip(), addr_2.strip()])
                else:
                    addr_full = addr_1

                properties = {
                    "ref": ref,
                    "name": name,
                    "addr_full": addr_full,
                    "city": response.xpath(
                        '//div[@class="Core-infoWrapper"]//span[@class="Address-field Address-city"]/text()'
                    ).extract_first(),
                    "postcode": response.xpath(
                        '//div[@class="Core-infoWrapper"]//span[@class="Address-field Address-postalCode"]/text()'
                    ).extract_first(),
                    "country": "GB",
                    "lat": response.xpath(
                        '//div[@class="Core-infoWrapper"]//span[@class="Address-coordinates"]/meta[@itemprop="latitude"]/@content'
                    ).extract_first(),
                    "lon": response.xpath(
                        '//div[@class="Core-infoWrapper"]//span[@class="Address-coordinates"]/meta[@itemprop="longitude"]/@content'
                    ).extract_first(),
                    "phone": response.xpath(
                        '//div[@class="Core-infoWrapper"]//span[@itemprop="telephone"]/text()'
                    ).extract_first(),
                    "website": response.url,
                }

                hours = response.xpath(
                    '//div[@class="Core-infoWrapper"]//@data-days'
                ).extract_first()
                if hours:
                    properties["opening_hours"] = self.store_hours(hours)

                yield GeojsonPointItem(**properties)
