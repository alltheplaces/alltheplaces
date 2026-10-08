import csv
import io
import lzma
import struct
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class UkrposhtaUASpider(Spider):
    name = "ukrposhta_ua"
    item_attributes = {"operator": "Укрпошта", "operator_wikidata": "Q2470783"}
    allowed_domains = ["data.gov.ua", "index.ukrposhta.ua"]
    # Ukrposhta publishes its postcode directory (every street/house mapped to the post office that serves it)
    # as open data. The newest file is listed first on the dataset page.
    DATASET = "https://data.gov.ua/dataset/e9b0cd40-a227-4e3f-9c05-1ec4b3f65115"
    API = "https://index.ukrposhta.ua/endpoints-for-apps/index.php?method="

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.DATASET, callback=self.parse_dataset)

    def parse_dataset(self, response: Response, **kwargs: Any) -> Any:
        url = response.xpath('//a[contains(@href, "/download/")]/@href').get()
        yield Request(url, callback=self.parse_directory)

    def parse_directory(self, response: Response, **kwargs: Any) -> Any:
        data = response.body
        if data.startswith(b"7z\xbc\xaf\x27\x1c"):
            # A single-file 7-Zip archive: the LZMA2-compressed file starts right after the 32 byte signature header
            # and runs up to the archive header. The dictionary must be at least as large as the one used to compress.
            (header_offset,) = struct.unpack("<Q", data[12:20])
            decompressor = lzma.LZMADecompressor(
                lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "dict_size": 1 << 26}]
            )
            data = decompressor.decompress(data[32 : 32 + header_offset])
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp1251")
        postcodes = {row["Postindex VPZ"].strip() for row in csv.DictReader(io.StringIO(text), delimiter=";")}
        for postcode in filter(None, postcodes):
            yield JsonRequest(
                f"{self.API}get_postoffices_by_postindex_web&pc={postcode}",
                callback=self.parse_offices,
                cb_kwargs={"postcode": postcode},
            )

    def parse_offices(self, response: Response, postcode: str) -> Any:
        offices = []
        for office in self.entries(response):
            if office["LOCK_CODE"] != "0":
                continue  # closed or temporarily not working (LOCK_UA explains why)
            if office["TYPE_ACRONYM"] == "ПВ":
                continue  # mobile post offices (vans) have no fixed location
            offices.append(office)
        if offices:
            yield JsonRequest(
                f"{self.API}get_postoffices_openhours_by_postindex&pc={postcode}",
                callback=self.parse_hours,
                cb_kwargs={"offices": offices},
                dont_filter=True,
                priority=1,
            )

    def parse_hours(self, response: Response, offices: list[dict]) -> Any:
        intervals = {}
        for interval in self.entries(response):
            intervals.setdefault(interval["id"], []).append(interval)
        for office in offices:
            item = Feature()
            item["ref"] = office["ID"]
            item["branch"] = office["PO_SHORT"]
            item["extras"]["official_name"] = office["PO_LONG"]
            item["lat"], item["lon"] = office["LATTITUDE"], office["LONGITUDE"]
            item["street"] = " ".join(
                filter(None, [self.text(office["STREETTYPE_UA"]), self.text(office["STREET_UA"])])
            )
            item["housenumber"] = self.text(office["HOUSENUMBER"])
            item["city"] = self.text(office["CITY_UA"])
            item["state"] = self.text(office["REGION_UA"])
            item["postcode"] = office["POSTINDEX"]
            item["opening_hours"] = self.opening_hours(intervals.get(office["ID"], []))
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def entries(response: Response) -> list[dict]:
        data = response.json()
        entries = data.get("Entry", []) if isinstance(data, dict) else data
        return entries if isinstance(entries, list) else [entries]

    @staticmethod
    def text(value: Any) -> str | None:
        # Empty values come through as {} (the API converts XML to JSON).
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def opening_hours(intervals: list[dict]) -> OpeningHours:
        # Per weekday: "W" is a working interval and "D" a lunch break inside it. "Тимчасовий" (temporary)
        # schedules replace the "Постійний" (permanent) ones while they apply.
        oh = OpeningHours()
        temporary = any(i["WORKCOMMENT"] == "Тимчасовий" for i in intervals)
        for day_num, day in enumerate(DAYS, start=1):
            day_intervals = [
                i
                for i in intervals
                if i["DAYOFWEEK_NUM"] == str(day_num) and (i["WORKCOMMENT"] == "Тимчасовий") == temporary
            ]
            breaks = sorted((i["TFROM"], i["TTO"]) for i in day_intervals if i["INTERVALTYPE"] == "D")
            for interval in day_intervals:
                if interval["INTERVALTYPE"] != "W":
                    continue
                start = interval["TFROM"]
                for break_start, break_end in breaks:
                    if start < break_start < interval["TTO"]:
                        oh.add_range(day, start, break_start)
                        start = break_end
                if start < interval["TTO"]:
                    oh.add_range(day, start, interval["TTO"])
        return oh
