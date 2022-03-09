import scrapy
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


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


class CreditUnionSpider(scrapy.Spider):

    name = "creditunion"
    download_delay = 0.5
    allowed_domains = ["co-opcreditunions.org"]

    def start_requests(self):
        base_url = "https://co-opcreditunions.org/locator/search-results/?loctype=S&state={state}&statewide=yes&country=&Submit=Search&lp=1"

        for state in STATES:
            url = base_url.format(state=state)
            yield scrapy.Request(url)

    def parse_hours(self, days):
        opening_hours = OpeningHours()
        for day in days:
            day = day.strip("\n ")
            if not day:
                continue
            parts = day.split(":")
            weekday = parts[0]
            hours = ":".join(parts[1:])
            try:
                open, close = hours.split("-")
                if (not open.strip()) or (open.strip() == "Closed"):
                    continue
                if close.strip() in ("24:00", "23:59"):  # two oddball banks
                    continue
                opening_hours.add_range(
                    day=weekday[:2],
                    open_time="{} AM".format(open.strip()),
                    close_time="{} PM".format(close.strip()),
                    time_format="%I:%M %p",
                )
            except:
                continue

        return opening_hours.as_opening_hours()

    def parse_bank(self, bank):

        address = bank.xpath(".//address/text()").extract()
        try:
            phone = address[3].strip()
        except IndexError:
            phone = ""

        href = bank.xpath(
            './/div[@class="location-results__share"]/div/a/@href'
        ).extract_first()
        lat, lon = re.search(r"lat=(.*?)&lng=(.*?)&", href).groups()
        name = bank.xpath(".//h3/text()").extract_first()
        ref = name + "-" + "-".join(address[0].split(" "))

        properties = {
            "name": name,
            "addr_full": address[0].strip(),
            "city": address[1].split(",")[0].strip(),
            "state": address[1].split(",")[1].strip(),
            "postcode": address[2].strip(),
            "phone": phone,
            "ref": ref,
            "website": bank.xpath("./div[1]/a/@href").extract_first(),
            "lat": float(lat),
            "lon": float(lon),
            "brand": name,
        }
        hours = self.parse_hours(
            bank.xpath(
                './/div[contains(@class, "location-results__hours")]/p/text()'
            ).extract()
        )
        if hours:
            properties["opening_hours"] = hours
        return properties

    def parse(self, response):
        page_num = int(re.search(r"lp=(\d+)$", response.url).groups()[0])
        pages = response.xpath(
            '//select[@class="locator-pager-select"]/option/text()'
        ).extract()
        if pages:
            max_page = max([int(p) for p in pages])
        else:
            max_page = 1

        banks = response.xpath('//div[@class="location-results"]/div')
        for bank in banks:
            properties = self.parse_bank(bank)
            yield GeojsonPointItem(**properties)

        if page_num < max_page:
            yield scrapy.Request(
                response.url.replace(
                    "lp={}".format(page_num), "lp={}".format(page_num + 1)
                )
            )
