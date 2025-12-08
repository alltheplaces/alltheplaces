import re
import time

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_CZ, DAYS_SK, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_email


class FioBankaSpider(CrawlSpider):
    name = "fio_banka"
    allowed_domains = ["www.fio.cz"]
    start_urls = ["https://www.fio.cz/kontakty"]
    rules = [
        Rule(LinkExtractor(allow=r"/kontakty\?&region=\d+")),
        Rule(
            LinkExtractor(
                allow=r"/o-nas/kontakty/",
                restrict_xpaths="//div[@id='tabContent-1']",
                # "Hypotecni centrum" is a duplicate branch to "Fio banka, Praha 1", same address but less info
                deny="https://www.fio.cz/o-nas/kontakty/316151-praha-1-hybernska-1033-7a-110-00-hypotecni-centrum",
            ),
            callback="parse",
            cb_kwargs={"country": "CZ"},
        ),
        Rule(
            LinkExtractor(allow=r"/o-nas/kontakty/", restrict_xpaths="//div[@id='tabContent-2']"),
            callback="parse",
            cb_kwargs={"country": "SK"},
        ),
    ]
    item_attributes = {
        "brand": "Fio banka",
        "brand_wikidata": "Q12016657",
    }

    def parse(self, response, country):
        item = Feature()
        item["ref"] = response.url.split("/")[-1].split("-")[0]
        item["name"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath("//tr[th[contains(text(), 'Ulice')]]/td/text()").get()
        city, postcode = response.xpath("//tr[th[contains(text(), 'Město')]]/td/text()").get().split(",")
        item["city"] = city.strip()
        item["postcode"] = postcode.strip()
        item["country"] = country
        item["website"] = response.url
        extract_email(item, response)
        extract_google_position(item, response)
        apply_category(Categories.BANK, item)

        # search phone number from the beginning, other text might be present
        # e.g. "224 346 938, 939, 940, linka 989 - pokladna"
        phone_line = response.xpath("//tr[th[contains(text(), 'Tel')]]/td/text()").get()
        if phone_line:
            item["phone"] = re.search(r"^[0-9\s+/]+", phone_line)[0].strip()

        hrs = response.xpath(
            "//*[h4[contains(text(), 'Otevírací') or contains(text(), 'Otváracie')]]//td/text()[normalize-space()]"
        ).get()
        if "CZ" == country:
            item["opening_hours"] = self.parse_opening_hours(hrs, DAYS_CZ)
        elif "SK" == country:
            item["opening_hours"] = self.parse_opening_hours(hrs, DAYS_SK)

        yield item

    def parse_opening_hours(self, text: str, days: dict) -> OpeningHours:
        oh = OpeningHours()
        # Example: "Po - Čt 8:30 - 18:00, Pá do 17:00"
        for row in text.split(","):
            if "do" in row and oh.day_hours:
                # if the text reads "do 17:00", copy the previous day's opening time
                last_day = list(oh.day_hours.values())[-1]
                first_entry = list(last_day)[0]
                open_time, _ = first_entry
                new_open_time = time.strftime("%H:%M", open_time)
                row = row.replace("do", new_open_time + " -")
            oh.add_ranges_from_string(row, days)
        return oh
