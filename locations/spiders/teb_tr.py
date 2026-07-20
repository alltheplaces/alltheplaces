import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature, set_closed


class TebTRSpider(Spider):
    name = "teb_tr"
    item_attributes = {"brand": "TEB", "brand_wikidata": "Q7862447"}
    custom_settings = {"USER_AGENT": "locations/1.0"}  # The default long Scrapy UA hangs on TEB.

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            url="https://www.teb.com.tr/en-yakin-teb-sube-atm/",
            callback=self.parse_finder,
        )

    def parse_finder(self, response: Response, **kwargs: Any) -> Any:
        branch_hours_text = response.xpath('normalize-space(//*[contains(@class, "subeBilgi")])').get()
        yield Request(
            url=(
                "https://www.teb.com.tr/moduls/servis/servisAjx.aspx?tip=liste"
                "&svt=167,&ulk=1&shr=&ilc=&lang=tr-TR&lat=&long=&itext="
            ),
            cb_kwargs={"location_type": "branch", "branch_hours_text": branch_hours_text},
        )
        yield Request(
            url=(
                "https://www.teb.com.tr/moduls/servis/servisAjx.aspx?tip=liste"
                "&svt=164,&ulk=1&shr=&ilc=&lang=tr-TR&lat=&long=&itext="
            ),
            cb_kwargs={"location_type": "atm"},
        )

    def parse(self, response: Response, location_type: str, branch_hours_text: str | None = None, **kwargs: Any) -> Any:
        for location in response.xpath('//*[contains(@class, "pServisListe")]'):
            if city_text := self.get_text(location, "divServisListe_UlkeSehirSemt"):
                if "KIBRIS" in city_text.upper() or "KKTC" in city_text.upper():
                    self.crawler.stats.inc_value(f"atp/{self.name}/skipped_non_tr")
                    continue

            source_name = self.get_text(location, "divServisListe_FirmaAdi")
            item = self.parse_location(location)
            if not item:
                continue

            service_type = self.get_text(location, "divServisListe_ServisTur") or ""

            if location_type == "branch":
                item["ref"] = "branch-{}".format(self.ref_from_name(source_name))
                item["branch"] = self.clean_branch(item.pop("name", None))
                item["phone"] = self.get_text(location, "divServisListe_Telefon")
                if opening_hours := self.branch_opening_hours(branch_hours_text):
                    item["opening_hours"] = opening_hours
                apply_yes_no(Extras.WHEELCHAIR, item, "engelsiz" in service_type.casefold())
                apply_category(Categories.BANK, item)

                if self.get_text(location, "divServisListe_GeciciKapali") == "E":
                    set_closed(item)
            elif location_type == "atm":
                item["ref"] = "atm-{}-{},{}".format(item.get("name"), item.get("lat"), item.get("lon"))
                apply_yes_no(Extras.WHEELCHAIR, item, "engelsiz" in service_type.casefold())
                apply_category(Categories.ATM, item)
            else:
                self.logger.error("Unexpected location type: {}".format(location_type))
                continue

            yield item

    def parse_location(self, location: Any) -> Feature | None:
        name = self.get_text(location, "divServisListe_FirmaAdi")
        coords = location.xpath('.//*[contains(@class, "divServisListe_Koordinat")]/a/@rel').get()
        lat, _, lon = (coords or "").partition("|")

        if not (name and lat and lon):
            self.logger.error("Missing name or coordinates in {}".format(location.get()))
            return None

        item = Feature(
            name=self.clean_name(name),
            lat=lat,
            lon=lon,
            addr_full=self.get_text(location, "divServisListe_Adres"),
        )

        if city_text := self.get_text(location, "divServisListe_UlkeSehirSemt"):
            item["city"] = city_text.rsplit("/", 1)[-1].strip()

        return item

    @staticmethod
    def branch_opening_hours(hours_text: str | None) -> OpeningHours | None:
        if not hours_text:
            return None
        try:
            if match := re.search(
                r"(?P<open_1>\d{1,2})[.:](?P<open_min_1>\d{2})\s*-\s*"
                r"(?P<close_1>\d{1,2})[.:](?P<close_min_1>\d{2}).*?"
                r"(?P<open_2>\d{1,2})[.:](?P<open_min_2>\d{2})\s*-\s*"
                r"(?P<close_2>\d{1,2})[.:](?P<close_min_2>\d{2})",
                hours_text,
            ):
                oh = OpeningHours()
                for day in DAYS_WEEKDAY:
                    oh.add_range(
                        day,
                        "{}:{}".format(match.group("open_1").zfill(2), match.group("open_min_1")),
                        "{}:{}".format(match.group("close_1").zfill(2), match.group("close_min_1")),
                    )
                    oh.add_range(
                        day,
                        "{}:{}".format(match.group("open_2").zfill(2), match.group("open_min_2")),
                        "{}:{}".format(match.group("close_2").zfill(2), match.group("close_min_2")),
                    )
                return oh
        except ValueError:
            return None
        return None

    @staticmethod
    def clean_branch(name: str | None) -> str | None:
        branch = re.sub(r"\s*\([^)]*\)\s*$", "", name or "").strip()
        return re.sub(r"\s*\w*ubesi$", "", branch, flags=re.IGNORECASE).strip()

    @staticmethod
    def clean_name(name: str | None) -> str | None:
        return re.sub(r"\s*\([^)]*\)\s*$", "", name or "").strip()

    @staticmethod
    def ref_from_name(name: str | None) -> str | None:
        if match := re.search(r"\(([^()]+)\)\s*$", name or ""):
            return match.group(1)
        return name

    @staticmethod
    def get_text(location: Any, class_name: str) -> str | None:
        return (
            " ".join(location.xpath('.//*[contains(@class, "{}")]/text()'.format(class_name)).getall()).strip() or None
        )
