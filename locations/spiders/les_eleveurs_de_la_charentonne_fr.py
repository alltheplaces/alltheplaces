import html
import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.hours import DAYS_FR, OpeningHours, day_range
from locations.items import Feature

DAYS = {name.lower(): day for name, day in DAYS_FR.items() if len(name) > 3}
DAY_NAMES = "|".join(DAYS)
TIME = r"(\d{1,2})h(\d{2})?"
TIME_RANGE = re.compile(rf"{TIME}\s*(?:-|à|a|\s)\s*{TIME}")


class LesEleveursDeLaCharentonneFRSpider(Spider):
    name = "les_eleveurs_de_la_charentonne_fr"
    item_attributes = {"brand": "Les Éleveurs de la Charentonne", "brand_wikidata": "Q130216320"}
    start_urls = ["https://www.leseleveursdelacharentonne.fr/nos-points-de-vente"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        # The store pages are only linked from the list page, keyed by the marker label.
        pages = {}
        for link in response.xpath('//a[@title="localiser ce magasin"]'):
            pages[link.xpath("normalize-space(text())").get()] = link.xpath("@href").get()
        yield Request(
            "https://www.leseleveursdelacharentonne.fr/nos-points-de-vente/ajax",
            callback=self.parse_markers,
            cb_kwargs={"pages": pages},
        )

    def parse_markers(self, response: Response, pages: dict[str, str]) -> Iterable[Feature]:
        for marker in response.xpath("//marker"):
            info = marker.xpath("infowindow/text()").get()
            # Partner shops of other brands are on the same map.
            if 'class="categorie">Point de vente<' not in info:
                continue
            label = marker.xpath("@label").get()

            item = Feature()
            item["ref"] = marker.xpath("@id").get()
            item["lat"] = marker.xpath("@lat").get()
            item["lon"] = marker.xpath("@lng").get()
            item["branch"] = re.sub(r"\s*\(\d+\)$", "", label)
            item["website"] = pages.get(label)

            lines = self.info_lines(info)
            address = next((line for line in lines if line.lower().startswith("nouvelle adresse")), lines[0])
            address = re.sub(r"\(.*?\)", "", address.split(":", 1)[-1] if "adresse" in address.lower() else address)
            item["addr_full"] = " ".join(address.split()).strip(" ,-")
            if postcode := re.search(r"\b(\d{5})\b(.*)", address):
                item["postcode"] = postcode.group(1)
                item["city"] = postcode.group(2).strip(" ,-") or None
            item["phone"] = next((line for line in lines if re.fullmatch(r"\d{2}(\.\d{2}){4}", line)), None)
            item["opening_hours"] = self.parse_hours(lines)

            yield item

    @staticmethod
    def info_lines(info: str) -> list[str]:
        body = info.split('class="categorie">Point de vente</span>', 1)[1]
        body = re.sub(r"<br\s*/?>|</?p>", "\n", body)
        body = html.unescape(re.sub(r"<[^>]+>", "", body))
        return [line.strip() for line in body.split("\n") if line.strip()]

    def parse_hours(self, lines: list[str]) -> OpeningHours | None:
        oh = OpeningHours()
        found = False
        for line in lines:
            if not re.search(DAY_NAMES, line.lower()):
                continue
            result = self.parse_hours_line(line)
            if result is None:
                self.logger.warning("Unparsed opening hours line: {}".format(line))
                return None
            days, ranges = result
            for day in days:
                if ranges:
                    for start, end in ranges:
                        oh.add_range(day, start, end)
                else:
                    oh.set_closed(day)
            found = found or bool(days)
        return oh if found else None

    @staticmethod
    def parse_hours_line(line: str) -> tuple[list[str], list[tuple[str, str]]] | None:
        text = line.lower().replace("&", " et ")
        for filler in ("sans interruption", "non-stop", "non stop"):
            text = text.replace(filler, " ")
        text = " ".join(text.split())

        if text.startswith("fermé"):
            # "Fermé le dimanche après-midi" only repeats the morning-only Sunday line.
            if "après-midi" in text:
                return [], []
            days_part, times_part = text.removeprefix("fermé"), "fermé"
        else:
            split = re.search(r"\d|fermé", text)
            if not split:
                return None
            days_part, times_part = text[: split.start()], text[split.start() :]

        # "Di mardi" is a typo for "Du mardi".
        days_part = re.sub(r"^(ouvert )?(du |le |di )?", "", days_part.strip())
        days_part = re.sub(r"\b(matin|de)\b|:", " ", days_part)
        days_part = " ".join(days_part.split())
        if match := re.fullmatch(rf"({DAY_NAMES}) (?:au|à) ({DAY_NAMES})", days_part):
            days = day_range(DAYS[match.group(1)], DAYS[match.group(2)])
        elif match := re.fullmatch(rf"({DAY_NAMES})(?: et ({DAY_NAMES}))?", days_part):
            days = [DAYS[name] for name in match.groups() if name]
        else:
            return None

        if "fermé" in times_part:
            return days, []
        ranges = []
        for start_h, start_m, end_h, end_m in TIME_RANGE.findall(times_part):
            ranges.append((f"{start_h}:{start_m or '00'}", f"{end_h}:{end_m or '00'}"))
        leftover = re.sub(r"\b(de|et|à)\b|[/,:]", " ", TIME_RANGE.sub(" ", times_part))
        if not ranges or leftover.strip():
            return None
        return days, ranges
