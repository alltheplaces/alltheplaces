import re
from time import strptime
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

BRANCH_LIST_URL = "https://www.fresnolibrary.org/branch/all.html"
CITY_STATE_POSTCODE_REGEX = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?$")
PHONE_REGEX = re.compile(r"\(?\d{3}\)?[ .-]?\d{3}-\d{4}")


class FresnoCountyPublicLibraryUSSpider(Spider):
    name = "fresno_county_public_library_us"
    item_attributes = {"operator": "Fresno County Public Library", "operator_wikidata": "Q2587462"}
    # The branch pages carry no coordinates, only Google Maps place links,
    # which are geocode results rather than pins the library published.
    start_urls = [BRANCH_LIST_URL]

    def parse(self, response: TextResponse) -> Iterable[Request]:
        for url in response.xpath('//td[@headers="Branch"]//a/@href').getall():
            url = response.urljoin(url)
            # The bookmobile is a vehicle rather than an outlet, and the links
            # out of /branch/ are the literacy service and the talking book
            # library, both departments of the Central Library.
            if url.startswith("https://www.fresnolibrary.org/branch/") and url not in (
                BRANCH_LIST_URL,
                "https://www.fresnolibrary.org/branch/bookmobile.html",
            ):
                yield Request(url, callback=self.parse_branch)

    def parse_branch(self, response: TextResponse) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.rsplit("/", 1)[-1].removesuffix(".html")
        item["website"] = response.url
        item["name"] = (response.css("h2.title::text").get() or "").strip()
        branch = re.sub(r"\s*(?:Branch|Regional)?\s*Library$", "", item["name"])
        if branch and branch != item["name"]:
            item["branch"] = branch

        # The address block ends at the "map" link. Anything after it is a
        # mailing address, and anything before it may be a closure notice or a
        # temporary pop-up location.
        lines = [" ".join(line.split()) for line in response.css("div.col-sm-7 ::text").getall()]
        lines = [line for line in lines if line]
        if "map" in lines:
            lines = lines[: lines.index("map")]
        for index in range(len(lines) - 1, -1, -1):
            if address := CITY_STATE_POSTCODE_REGEX.fullmatch(lines[index]):
                item["city"], item["state"], item["postcode"] = address.groups()
                item["street_address"] = next(
                    (line for line in reversed(lines[max(index - 2, 0) : index]) if line[:1].isdigit()), None
                )
                item["phone"] = next(
                    (phone.group(0) for line in lines[index + 1 :] if (phone := PHONE_REGEX.search(line))), None
                )
                break

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//tr[td[@class="n"]]'):
            cells = [" ".join(cell.split()) for cell in row.xpath('./td[@class="n"]//text()').getall()]
            if len(cells := [cell for cell in cells if cell]) != 2:
                continue
            day, times = cells
            if times.lower() == "closed":
                item["opening_hours"].set_closed(day)
                continue
            # A day is either one range, or a morning and an afternoon session
            # separated by "&" or a comma, e.g. "10am - 12pm, 1pm - 6pm".
            for session in re.split(r"\s*[&,]\s*", times):
                start, _, end = session.partition("-")
                start, end = strptime(start.strip(), "%I%p"), strptime(end.strip(), "%I%p")
                if start < end:
                    item["opening_hours"].add_range(day, start, end)
                else:
                    # Mendota publishes "10pm - 6pm" for one day where every
                    # other source, including LibCal, says 10am. Keeping it
                    # would run the range over midnight and take the next day
                    # with it, so the day is left unknown instead.
                    self.logger.warning("Ignoring reversed hours for %s on %s: %s", item["ref"], day, session)

        apply_category(Categories.LIBRARY, item)
        yield item
