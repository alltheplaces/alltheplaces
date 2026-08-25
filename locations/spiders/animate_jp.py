import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAY_ABBR = {
    "mon": "Mo",
    "tue": "Tu",
    "wed": "We",
    "thu": "Th",
    "fri": "Fr",
    "sat": "Sa",
    "sun": "Su",
}

# Matches day ranges such as "Mon-Thu", "Mon–Thu", "Saturday-Sunday" or
# "Sun～Thur" (a full/half width wave dash is sometimes used in place of a
# hyphen on the translated pages of this site).
DAY_RANGE_RE = re.compile(r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\s*[-–—~〜～]\s*(mon|tue|wed|thu|fri|sat|sun)[a-z]*\b")

# Matches a time range, e.g. "10:00-21:00", "10:00～21:00", "11:00 AM – 8:00 PM"
# or "10:00 AM to 9:00 PM". A full/half width wave dash or colon is sometimes
# used instead of the ASCII equivalent on the translated pages of this site.
TIME_RANGE_RE = re.compile(
    r"(\d{1,2})[:.：](\d{2})\s*([AaPp]\.?[Mm]\.?)?"
    r"\s*(?:[-–—~〜～]|to)\s*"
    r"(\d{1,2})[:.：](\d{2})\s*([AaPp]\.?[Mm]\.?)?"
)

# Matches the first phone number found in a string. Some pages append extra
# notes after (or, rarely, before) the phone number itself, e.g.
# "047-403-2424　※Please note that we cannot be reached outside of business
# hours." or "animate Omiya Building 1 (Character Goods)　048-646-0320;...".
# A Unicode hyphen ("‐", as opposed to an ASCII hyphen-minus) is sometimes
# used between the area code and the rest of the number, e.g. "052‐684-8877".
PHONE_RE = re.compile(r"\+?\d[\d\-‐\s]{5,}\d")


def _to_24h(hour: str, minute: str, meridiem: str | None) -> str:
    hour_int = int(hour)
    if meridiem and hour_int <= 12:
        meridiem = meridiem.upper().replace(".", "")
        if hour_int == 12:
            hour_int = 0
        if meridiem == "PM":
            hour_int += 12
    return f"{hour_int:02d}:{minute}"


def _extract_days(context: str) -> list[str] | None:
    context = context.lower()

    if m := DAY_RANGE_RE.search(context):
        start, end = DAY_ABBR[m.group(1)], DAY_ABBR[m.group(2)]
        start_index, end_index = DAYS.index(start), DAYS.index(end)
        if start_index <= end_index:
            return DAYS[start_index : end_index + 1]
        return DAYS[start_index:] + DAYS[: end_index + 1]

    if "weekday" in context and "weekend" not in context:
        return ["Mo", "Tu", "We", "Th", "Fr"]
    if "weekend" in context:
        return ["Sa", "Su"]

    found = [code for abbr, code in DAY_ABBR.items() if re.search(r"\b" + abbr + r"[a-z]*\b", context)]
    if found:
        return [day for day in DAYS if day in found]

    if any(keyword in context for keyword in ("all day", "daily", "every day")):
        return list(DAYS)

    return None


def parse_hours(text: str) -> OpeningHours | None:
    """
    Parses the free text "Business Hours" field found on animate.co.jp shop
    pages. Formats seen include a single blanket time range covering every
    day of the week, and ranges qualified by a preceding day/day-range label
    (e.g. "Weekdays 10:00-20:00 Weekends & Holidays 10:00-21:00"). Some pages
    also list unrelated hours for an in-store cafe alongside the main shop's
    hours; when no day labels can be found anywhere in the string, only the
    first time range (which always corresponds to the shop itself) is used.
    """
    matches = list(TIME_RANGE_RE.finditer(text))
    if not matches:
        return None

    labelled_ranges = []
    position = 0
    for match in matches:
        labelled_ranges.append((_extract_days(text[position : match.start()]), match))
        position = match.end()

    oh = OpeningHours()

    if all(days is None for days, _ in labelled_ranges):
        _, match = labelled_ranges[0]
        oh.add_days_range(DAYS, _to_24h(*match.group(1, 2, 3)), _to_24h(*match.group(4, 5, 6)))
        return oh

    for days, match in labelled_ranges:
        if not days:
            continue
        oh.add_days_range(days, _to_24h(*match.group(1, 2, 3)), _to_24h(*match.group(4, 5, 6)))

    return oh or None


class AnimateJPSpider(SitemapSpider):
    name = "animate_jp"
    item_attributes = {"brand": "アニメイト", "brand_wikidata": "Q1041890"}
    sitemap_urls = ["https://www.animate.co.jp/shop-sitemap.xml"]
    sitemap_rules = [(r"/shop/[^/]+/$", "parse")]

    # Almost all shops are in Japan (implied by the spider name), but a
    # number of overseas shops (see the "Store finder url(s)" sitemap) are
    # not, so the country of each of these needs to be set explicitly
    # rather than relying on the default derived from the spider's name.
    OVERSEAS_COUNTRIES = {
        "bangkok": "TH",
        "futureparkrangsit": "TH",
        "beijing": "CN",
        "chengdu": "CN",
        "guangzhou": "CN",
        "hangzhou": "CN",
        "shanghai": "CN",
        "wujiaochang": "CN",
        "xiamen": "CN",
        "busan": "KR",
        "hongdae": "KR",
        "jamsillotte": "KR",
        "suwon": "KR",
        "hongkong": "HK",
        "kaohsiung": "TW",
        "kaohsiung-station": "TW",
        "taichung": "TW",
        "taipei": "TW",
        "ximen": "TW",
        "kualalumpur": "MY",
        "losangeles": "US",
    }

    NAME_XPATH = (
        '//div[@data-headline="shop"]//h1//text()'
        ' | //div[contains(@class, "ikebukuroIndexHeroTitleSubText")]//text()'
    )
    ADDRESS_XPATH = (
        '//dt[normalize-space()="Address"]/following-sibling::dd[1]/p[1]//text()'
        ' | //th[normalize-space()="Address"]/following-sibling::td[1]//text()'
    )
    PHONE_XPATH = (
        '//dt[normalize-space()="Phone Number"]/following-sibling::dd[1]/p[1]//text()'
        ' | //th[normalize-space()="Phone Number"]/following-sibling::td[1]//text()'
    )
    HOURS_XPATH = (
        '//dt[normalize-space()="Business Hours"]/following-sibling::dd[1]//text()'
        ' | //th[normalize-space()="Business Hours"]/following-sibling::td[1]//text()'
    )

    def sitemap_filter(self, entries):
        # Request the English translation of each shop page. Layout and
        # labelling is consistent across all languages the site supports,
        # but English allows for reliable parsing without relying on
        # multi-language day/hour vocabulary.
        for entry in entries:
            entry["loc"] = entry["loc"].replace("animate.co.jp/shop/", "animate.co.jp/en/shop/")
            yield entry

    def parse(self, response: Response):
        name = " ".join(response.xpath(self.NAME_XPATH).getall())
        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            return
        # A small number of pages have their heading text duplicated by
        # mistake at the source, e.g. "animate Gifuanimate Gifu".
        half = len(name) // 2
        if len(name) % 2 == 0 and name[:half] == name[half:]:
            name = name[:half]

        address = " ".join(response.xpath(self.ADDRESS_XPATH).getall()).strip()
        address = re.sub(r"\s+", " ", address)
        address = re.sub(r"^〒\S*\s*", "", address).strip()
        if not address:
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # Explicitly set the brand name rather than relying on it being
        # applied automatically from a matching NSI entry, since NSI does
        # not have location coverage for the shops outside of Japan.
        item["name"] = self.item_attributes["brand"]
        item["branch"] = re.sub(r"(?i)^animate\s+", "", name).strip() or name
        item["addr_full"] = address
        item["country"] = self.OVERSEAS_COUNTRIES.get(item["ref"], "JP")
        item["website"] = response.url.replace("/en/shop/", "/shop/")

        phone = " ".join(response.xpath(self.PHONE_XPATH).getall()).strip()
        if phone and phone != "-":
            if m := PHONE_RE.search(phone):
                item["phone"] = m.group(0).strip()

        extract_google_position(item, response)

        hours_text = " ".join(response.xpath(self.HOURS_XPATH).getall())
        hours_text = re.sub(r"\s+", " ", hours_text).strip()
        if hours_text:
            if oh := parse_hours(hours_text):
                item["opening_hours"] = oh

        apply_category(Categories.SHOP_ANIME, item)

        if item.get("lat") is None:
            # A small number of pages (e.g. flagship stores) use a
            # different template without an embedded Google Maps iframe,
            # but the coordinates are available from the "access" subpage.
            yield response.follow("access/", callback=self.parse_access_geometry, cb_kwargs={"item": item})
        else:
            yield item

    def parse_access_geometry(self, response: Response, item: Feature):
        extract_google_position(item, response)
        yield item
