import re
from typing import Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import Request, TextResponse
from w3lib.html import remove_tags

from locations.categories import Categories, Extras, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

CITY_STATE_POSTCODE_REGEX = re.compile(r"(.+?)\s*,?\s+(?:MN|Minnesota)\s+(\d{5})", re.IGNORECASE)
PHONE_REGEX = re.compile(r"\(?\d{3}\)?[ .-]*\d{3}[ .-]*\d{4}")


class PioneerlandLibrarySystemUSSpider(Spider):
    name = "pioneerland_library_system_us"
    item_attributes = {"operator": "Pioneerland Library System", "operator_wikidata": "Q69480753"}
    # The member sites have no map or other coordinate source.
    start_urls = ["https://www.pioneerland.lib.mn.us/member-libraries/"]

    def parse(self, response: TextResponse) -> Iterable[Request]:
        for url in response.xpath('//a[contains(@href, ".lib.mn.us") or contains(@href, "willmar")]/@href').getall():
            host = urlparse(url).hostname
            if host and host.startswith("www.") and host != "www.pioneerland.lib.mn.us":
                yield Request(f"https://{host}/", callback=self.parse_library)

    def parse_library(self, response: TextResponse) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = urlparse(response.url).hostname
        item["website"] = response.url

        for widget in response.css("div.rightwidget"):
            # Split per line rather than per text node, as Willmar writes "5<sup>th</sup> Street".
            lines = [widget.css("h2.widgettitle::text").get("")] + re.split(
                r"<br\s*/?>|</p>", widget.css("div.textwidget").get("")
            )
            lines = [" ".join(remove_tags(line).split()).strip(" ,") for line in lines]
            lines = [line for line in lines if line]
            city_line = next((i for i, line in enumerate(lines) if CITY_STATE_POSTCODE_REGEX.fullmatch(line)), None)
            if city_line is None:
                continue
            item["name"] = next(line for line in lines if line.endswith("Library"))
            item["city"], item["postcode"] = CITY_STATE_POSTCODE_REGEX.fullmatch(lines[city_line]).groups()
            item["state"] = "MN"
            item["street_address"] = next(line for line in lines[:city_line] if line[:1].isdigit())
            fax = None
            for line in lines[city_line + 1 :]:
                if not (phone := PHONE_REGEX.search(line)):
                    continue
                if "fax" in line.lower():
                    fax = phone.group(0)
                elif not item.get("phone"):
                    item["phone"] = phone.group(0)
            # Dawson and Milan list the same number for phone and fax.
            if fax and re.sub(r"\D", "", fax) != re.sub(r"\D", "", item.get("phone") or ""):
                item["extras"][Extras.FAX.value] = fax
            break

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//tr[td[@class="LHours_Day"]]'):
            day, *times = [t.replace("\u200e", "").strip() for t in row.xpath("./td//text()").getall()]
            if times == ["Closed"]:
                item["opening_hours"].set_closed(day)
                continue
            # Times are 12-hour without am/pm. An opening time from 1:00 to 7:00 and
            # a closing time at or before the opening time are in the afternoon.
            (open_hour, open_minute), (close_hour, close_minute) = [map(int, t.split(":")) for t in times]
            if 1 <= open_hour <= 7:
                open_hour += 12
            if (close_hour, close_minute) <= (open_hour, open_minute):
                close_hour += 12
            item["opening_hours"].add_range(
                day, f"{open_hour}:{open_minute:02}", f"{close_hour}:{close_minute:02}", time_format="%H:%M"
            )

        apply_category(Categories.LIBRARY, item)
        yield item
