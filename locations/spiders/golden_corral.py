import json
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from urllib.parse import urljoin, urlparse

DAY_MAPPING = {
    "Sunday": "Su",
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
}


class GoldenCorralSpider(scrapy.Spider):
    name = "golden_corral"
    item_attributes = {"brand": "Golden Corral"}
    allowed_domains = ["goldencorral.com"]
    download_delay = 0.5
    start_urls = ("https://www.goldencorral.com/all-locations",)

    def parse(self, response):
        item_list = response.xpath('//*[@itemtype="http://schema.org/ItemList"]')
        all_locations = item_list.xpath('//*[@itemtype="http://schema.org/Restaurant"]')

        for loc in all_locations:
            url = loc.xpath('.//*[@itemprop="url"]/@href').get()
            url_parsed = urlparse(url)
            if not url_parsed.scheme or not url_parsed.netloc:
                url = urljoin(response.url, url)
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        data = self.get_json_data(response)
        if not data:
            # In case we reached a URL that does not provide details of an individual store
            return

        data_address = data.get("address")
        data_geo = data.get("geo")

        if not data_address or not data_geo:
            return

        properties = {
            # The path of store URLs look like '/locations/<store_number>/<store_name>'.
            # Extract the store number from this path.
            "ref": urlparse(data["url"]).path.split("/")[2],
            "name": data["name"],
            "addr_full": data_address["streetAddress"],
            "city": data_address["addressLocality"],
            "state": data_address["addressRegion"],
            "postcode": data_address["postalCode"],
            "country": data_address["addressCountry"],
            "lon": float(data_geo["longitude"]),
            "lat": float(data_geo["latitude"]),
            "phone": data["telephone"],
            "website": data["url"],
            "opening_hours": parse_hours(data["openingHoursSpecification"]),
        }

        yield GeojsonPointItem(**properties)

    def get_json_data(self, response):
        # The pages for each location include JSON data in several <script /> blocks.
        # The metadata for the location is in the block that follows the Restaurant
        # schema (see http://schema.org/Restaurant).
        all_ldjson = response.xpath('//*/script[@type="application/ld+json"]/text()')
        for ldjson in all_ldjson:
            data = json.loads(ldjson.get())
            if data["@type"] == "Restaurant":
                return data

        return


def adjust_closing_time(time_str):
    if time_str == "00:00":
        time_str = "23:59"

    return time_str


def parse_hours(hours_json):
    opening_hours = OpeningHours()

    for spec in hours_json:
        for day in spec["dayOfWeek"]:
            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time=remove_seconds(spec["opens"]),
                close_time=adjust_closing_time(remove_seconds(spec["closes"])),
            )

    return opening_hours.as_opening_hours()


def remove_seconds(time_str):
    # Time specifications may appear as HH:MM:SS.  If so, remove the ":SS".
    if time_str.count(":") == 2:
        time_str = time_str.rsplit(":", 1)[0]

    return time_str
