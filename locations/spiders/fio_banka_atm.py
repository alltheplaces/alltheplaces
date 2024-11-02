import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import DAYS, DAYS_CZ, DAYS_SK, OpeningHours
from locations.items import Feature


class FioBankaAtmSpider(CrawlSpider):
    name = "fio_banka_atm"
    allowed_domains = ["www.fio.cz", "www.fio.sk"]
    start_urls = [
        "https://www.fio.cz/kontakty",
        "https://www.fio.sk/kontakty",
    ]
    rules = [Rule(LinkExtractor(allow=r"/kontakty\?&region=\d+"), callback="parse")]
    item_attributes = {
        "brand": "Fio banka",
        "brand_wikidata": "Q12016657",
        "operator": "Fio banka",
        "operator_wikidata": "Q12016657",
    }
    no_refs = True

    def parse(self, response):
        rows = response.xpath("//div[@class='results']//tr")
        # 3 table lines correspond to a single branch
        for line1, line2 in self.batched(rows, 2):
            item = Feature()
            header = line1.xpath(".//h3/text()").get()
            item["name"] = header
            item["city"] = (
                header.replace("(bankomat i vkladomat)", "").replace("(bankomat aj vkladomat)", "").strip(" -")
            )
            extract_google_position(item, line1)
            item["street_address"] = line2.xpath(".//strong/text()").get()

            apply_category(Categories.ATM, item)

            if "lat" not in item:
                lat, lon = line1.xpath(".//td[contains(text(), 'GPS')]/text()").get().removeprefix("GPS:").split(",")
                item["lat"] = self.parse_coordinates(lat)
                item["lon"] = self.parse_coordinates(lon)

            if "fio.cz" in response.url:
                item["country"] = "CZ"
            elif "fio.sk" in response.url:
                item["country"] = "SK"

            hrs = line2.xpath(".//li[3]/text()").get()
            if hrs:
                if "CZ" == item["country"]:
                    item["opening_hours"] = self.parse_opening_hours(hrs, DAYS_CZ)
                elif "SK" == item["country"]:
                    item["opening_hours"] = self.parse_opening_hours(hrs, DAYS_SK)

            if "vkladomat" in header:
                apply_yes_no(Extras.CASH_IN, item, True)

            yield item

    def parse_opening_hours(self, text: str, days: dict) -> OpeningHours:
        oh = OpeningHours()
        if "nonstop" in text.lower():
            oh.add_days_range(DAYS, "00:00", "24:00")
        else:
            # remove holiday as ATP cannot currently parse PH
            text = text.replace("/svátky", "")
            oh.add_ranges_from_string(text, days)
        return oh

    # polyfill for itertools
    # TODO: replace with itertools.batched in Python 3.12
    def batched(self, iterable, n):
        iterators = [iter(iterable)] * n
        return zip(*iterators)

    def parse_coordinates(self, text: str) -> float:
        # "49.4747139N" or "48°58.45678N" or "49°05'04.6"N"
        deg, min, sec = re.search(r"(\d+(?:\.\d+)?)(?:°(\d+(?:\.\d+)?)(?:'(\d+(?:\.\d+)?)\")?)?", text).groups()
        if not deg:
            return None
        if not min:
            return float(deg)
        if not sec:
            return float(deg) + float(min) / 60
        return float(deg) + float(min) / 60 + float(sec) / 3600
