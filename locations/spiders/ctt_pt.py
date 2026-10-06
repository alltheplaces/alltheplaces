import math
import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

BASE_URL = "https://appserver2.ctt.pt/feapl_2/app/open/stationSearch/search.jspx"
PAGE_SIZE = 5  # Fixed by the site; no page size parameter is honoured.

DAY_NAMES = {
    "2ª": DAYS[0],
    "segunda-feira": DAYS[0],
    "3ª": DAYS[1],
    "terça-feira": DAYS[1],
    "4ª": DAYS[2],
    "quarta-feira": DAYS[2],
    "5ª": DAYS[3],
    "quinta-feira": DAYS[3],
    "6ª": DAYS[4],
    "sexta-feira": DAYS[4],
    "sábado": DAYS[5],
    "domingo": DAYS[6],
}


class CttPTSpider(Spider):
    """
    CTT's "Pontos CTT" finder. Searches need at least a district, results come 5 per page and paging is
    stateless (the search fields are re-sent with `currentPage`), so each district's pages are fetched directly.

    Station types: RECET = letter boxes (marcos e caixas), EC = CTT post offices (Loja CTT), PC = post offices
    run by partners (Ponto CTT / "Loja CTT em parceria"), PARC = partner shops that only hand out and accept
    parcels (not collected).
    """

    name = "ctt_pt"
    item_attributes = {"operator": "CTT", "operator_wikidata": "Q1024518"}
    allowed_domains = ["appserver2.ctt.pt"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    station_types = ["RECET", "EC,PC"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest("https://appserver2.ctt.pt/scref/countries/pt/districts", callback=self.parse_districts)

    def parse_districts(self, response: Response, **kwargs: Any) -> Any:
        for district in response.json():
            for station_type in self.station_types:
                yield self.search_request(district["code"], station_type, 1)

    def search_request(self, district: str, station_type: str, page: int) -> FormRequest:
        formdata = {"stationType": station_type, "district": district, "municipality": "", "parish": "", "location": ""}
        if page > 1:
            formdata.update({"resultsOnly": "true", "currentPage": str(page)})
        return FormRequest(
            BASE_URL,
            formdata=formdata,
            callback=self.parse_results,
            cb_kwargs={"district": district, "station_type": station_type, "page": page},
            meta={"cookiejar": f"{district}-{station_type}"},
            dont_filter=True,
        )

    def parse_results(self, response: Response, district: str, station_type: str, page: int) -> Any:
        if page == 1:
            total = response.xpath('//p[contains(., "Foram encontrados")]/strong/text()').re_first(r"(\d+)")
            if total is None:
                self.crawler.stats.inc_value("atp/ctt_pt/no_results")
                return
            for next_page in range(2, math.ceil(int(total) / PAGE_SIZE) + 1):
                yield self.search_request(district, station_type, next_page)

        for entry in response.xpath('//li[@class="entry-wrapper"]//div[@class="entry-content"]'):
            if station_type == "RECET":
                yield from self.parse_box(entry)
            else:
                yield from self.parse_office(entry)

    @staticmethod
    def set_coordinates(item: Feature, entry) -> None:
        if coords := entry.xpath('.//a[contains(@href, "pointSearchResultsMap")]/@href').re_first(r"q=([^&]+)"):
            lat, lon = coords.split(",")
            item["lat"], item["lon"] = float(lat), float(lon)

    def parse_box(self, entry) -> Any:
        item = Feature()
        self.set_coordinates(item, entry)
        if not item.get("lat"):
            self.crawler.stats.inc_value("atp/ctt_pt/box_without_coordinates")
            return
        # Point codes (RECET1983957) are a contiguous run over the whole country, so they look like they are
        # renumbered on each monthly data refresh. The coordinates are used as the reference instead.
        item["ref"] = f"{item['lat']:.6f},{item['lon']:.6f}"

        location = " ".join(
            " ".join(
                entry.xpath('.//div[@class="posRelative"]/b[text()="Localização"]/following-sibling::text()').getall()
            ).split()
        ).lstrip(": ")
        if m := re.match(r"(.*?)\s+(\d{4}-\d{3})\s+(.+)$", location):
            item["street_address"], item["postcode"], item["city"] = m.group(1).strip(" ,"), m.group(2), m.group(3)
        else:
            item["street_address"] = location

        # Last collection: Mon-Fri priority mail, Mon-Fri normal mail, Saturday, Sunday.
        times = [t.strip() for t in entry.xpath('.//td[@class="mailboxScheduleLine"]/text()').getall()]
        # "-" means no collection; "00:00" only appears as a placeholder (Selvagens Islands).
        times = [t.zfill(5) if re.fullmatch(r"\d{1,2}:\d{2}", t) and t != "00:00" else None for t in times]
        if len(times) == 4:
            priority, normal, saturday, sunday = times
            collection_times = []
            if weekday := max(filter(None, [priority, normal]), default=None):
                collection_times.append(f"Mo-Fr {weekday}")
            if saturday:
                collection_times.append(f"Sa {saturday}")
            if sunday:
                collection_times.append(f"Su {sunday}")
            if collection_times:
                item["extras"]["collection_times"] = "; ".join(collection_times)

        apply_category(Categories.POST_BOX, item)
        yield item

    def parse_office(self, entry) -> Any:
        kind = entry.xpath("./p[1]/text()").get("").strip()
        name = " ".join(entry.xpath("./h3//text()").get("").split())
        item = Feature()
        item["ref"] = entry.xpath('.//a[@class="collapsible-open"]/@onclick').re_first(r"\((\d+)\)")
        self.set_coordinates(item, entry)

        address_lines = [
            " ".join(t.split()) for t in entry.xpath('.//div[@class="posRelative"]/text()').getall() if t.strip()
        ]
        if address_lines:
            item["street_address"] = address_lines[0]
            for line in address_lines[1:]:
                if m := re.match(r"(\d{4}-\d{3})\s+(.+)$", line):
                    item["postcode"], item["city"] = m.group(1), m.group(2)
        item["phone"] = entry.xpath('.//a[starts-with(@href, "tel:")]/text()').get()
        item["opening_hours"] = self.parse_hours(entry)

        if kind == "Loja CTT":
            item["brand"], item["brand_wikidata"] = "CTT", "Q1024518"
            item["branch"] = name.removeprefix("Loja CTT").strip()
            item["name"] = "CTT"
            apply_category(Categories.POST_OFFICE, item)
        elif kind == "Loja CTT em parceria":
            # Post office counters run by a partner business (shop, parish council, ...).
            item["name"] = name
            item["extras"]["post_office"] = "post_partner"
            apply_category(Categories.GENERIC_POI, item)
        else:
            self.crawler.stats.inc_value(f"atp/ctt_pt/unmapped_kind/{kind}")
            return
        yield item

    @staticmethod
    def parse_days(label: str) -> list[str] | None:
        """Parse "Dias úteis", "2ª a 5ª", "sábado , domingo e feriados", "2ª a domingo e feriados", ... (holidays are dropped)."""
        days = []
        for part in re.split(r",| e ", label.strip().lower()):
            part = part.strip()
            if part == "dias úteis":
                days += DAYS[:5]
            elif part == "feriados":
                continue
            elif " a " in part:
                first, last = (DAY_NAMES.get(d.strip()) for d in part.split(" a ", 1))
                if not first or not last:
                    return None
                days += DAYS[DAYS.index(first) : DAYS.index(last) + 1]
            elif part in DAY_NAMES:
                days.append(DAY_NAMES[part])
            else:
                return None
        return days

    def parse_hours(self, entry) -> OpeningHours:
        oh = OpeningHours()
        for rule in entry.xpath('.//h4[text()="Horário"]/following-sibling::ul[@class="list-check"]/li'):
            text = " ".join(" ".join(rule.xpath(".//text()").getall()).split())
            label, _, ranges = text.partition(":")
            days = self.parse_days(label)
            if days is None:
                self.crawler.stats.inc_value(f"atp/ctt_pt/unknown_day_label/{label.strip()}")
                continue
            for open_time, close_time in re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", ranges):
                for day in days:
                    oh.add_range(day, open_time, close_time)
        return oh
