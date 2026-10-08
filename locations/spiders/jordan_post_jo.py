import csv
import io
import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.geo import bbox_contains
from locations.items import Feature

# Open Government Data Portal datasets published by Jordan Post under the Open Jordanian License.
# Both CSVs list the same offices in the same order under the same serial number ("التسلسل").
COORDINATES_CSV = (
    "https://opendata.gov.jo/dataset/MIGRATED-2832-2023/resource/188cfcbf-97b2-452f-bf68-25b2c777d1da/download/-.csv"
)
ADDRESSES_CSV = (
    "https://opendata.gov.jo/dataset/MIGRATED-2830-2023/resource/045690bf-83f2-4175-8b91-8343a537c3e4/download/-.csv"
)
# (min_lon, min_lat, max_lon, max_lat) of Jordan, with a little slack.
JORDAN_BBOX = (34.8, 29.1, 39.4, 33.4)
DMS_RE = re.compile(r"(\d+)\s*°\s*(\d+)\s*'\s*([\d.]+)\s*\"")
DECIMAL_RE = re.compile(r"\d+\.\d+")
HOURS_RE = re.compile(r"^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$")


class JordanPostJOSpider(Spider):
    name = "jordan_post_jo"
    item_attributes = {"operator": "البريد الأردني", "operator_wikidata": "Q6276895"}
    allowed_domains = ["opendata.gov.jo"]
    start_urls = [COORDINATES_CSV]
    # opendata.gov.jo/robots.txt asks for a 3 second crawl delay.
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_DELAY": 3}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        coordinates = {row[0]: row for row in self.read_rows(response)}
        yield Request(url=ADDRESSES_CSV, callback=self.parse_addresses, cb_kwargs={"coordinates": coordinates})

    def parse_addresses(self, response: Response, coordinates: dict[str, list[str]], **kwargs: Any) -> Any:
        addresses = {row[0]: row for row in self.read_rows(response)}
        for serial, row in coordinates.items():
            # Columns: serial, directorate, office name, postal code, coordinates (free text).
            _, _, office, postcode, location = (row + [""] * 5)[:5]
            item = Feature()
            item["ref"] = serial
            item["branch"] = office
            item["lat"], item["lon"] = self.parse_coordinates(location)
            if re.fullmatch(r"\d{5}", postcode):
                item["postcode"] = postcode
            item["extras"] = {"operator:en": "Jordan Post"}
            if address_row := addresses.get(serial):
                # Columns: serial, directorate, office name, working hours, address ("city/district/street").
                _, _, _, hours, address = (address_row + [""] * 5)[:5]
                item["addr_full"] = address or None
                # Only a daily time window is given ("8:30-15:30"); the working days are not stated,
                # so it is not turned into an opening_hours schedule.
                if HOURS_RE.match(hours):
                    item["extras"]["working_hours"] = re.sub(r"\s+", "", hours)
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def read_rows(response: Response) -> list[list[str]]:
        # The CSVs open with a title line and a blank line before the header row; data rows start
        # with a numeric serial.
        reader = csv.reader(io.StringIO(response.body.decode("utf-8-sig")))
        return [[cell.strip() for cell in row] for row in reader if row and row[0].strip().isdigit()]

    def parse_coordinates(self, text: str) -> tuple[float | None, float | None]:
        # Mostly decimal "lat lon" or "lat, lon"; a few are degrees-minutes-seconds, a few are blank
        # or broken (e.g. the latitude repeated as the longitude).
        if dms := DMS_RE.findall(text):
            values = [int(d) + int(m) / 60 + float(s) / 3600 for d, m, s in dms]
        else:
            values = [float(value) for value in DECIMAL_RE.findall(text)]
        if len(values) != 2:
            if text:
                self.crawler.stats.inc_value("atp/{}/coordinates/unparsed".format(self.name))
            return None, None
        lat, lon = values
        if bbox_contains(JORDAN_BBOX, (lon, lat)):
            return lat, lon
        if bbox_contains(JORDAN_BBOX, (lat, lon)):
            self.crawler.stats.inc_value("atp/{}/coordinates/swapped".format(self.name))
            return lon, lat
        self.crawler.stats.inc_value("atp/{}/coordinates/outside_jordan".format(self.name))
        return None, None
