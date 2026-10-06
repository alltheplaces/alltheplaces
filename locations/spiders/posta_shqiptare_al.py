import re
from typing import Any

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAY_LABELS = {
    "e hënë - e premte": DAYS[:5],
    "e shtunë": ["Sa"],
    "e diel": ["Su"],
}
# Times are written loosely: "07.30:15.30", "08.00 : 16.30", "07. 20:20.00", "08:00-14:00", "08.00 : 1600".
TIME_RE = re.compile(r"(\d{1,2})\s*[.:;]?\s*(\d{2})(?!\d)")


class PostaShqiptareALSpider(Spider):
    name = "posta_shqiptare_al"
    item_attributes = {"operator": "Posta Shqiptare", "operator_wikidata": "Q1334419"}
    allowed_domains = ["www.postashqiptare.al"]

    async def start(self):
        # The network map (https://www.postashqiptare.al/rrjeti) posts a municipality filter here;
        # an empty filter returns every branch as an HTML fragment.
        yield FormRequest("https://www.postashqiptare.al/functions/deget.php", formdata={"q": ""})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for branch in response.xpath('//div[@class="branch"]'):
            ref = branch.xpath("@id").re_first(r"branch(\d+)")
            name = branch.xpath("normalize-space(.//h4)").get()
            if name.startswith("Drejtoria e Përgjithshme"):
                continue  # head office (administration), not a counter
            lines = [p.xpath("normalize-space()").get() for p in branch.xpath('.//div[@class="b-info"]/p')]
            address, postcode, phone, *hours = lines + [""] * (6 - len(lines))

            item = Feature()
            item["ref"] = ref
            item["branch"] = name
            coords = response.xpath(f'//input[@class="markers"][@data-id="{ref}"]/@value').get("")
            if "," in coords:
                item["lat"], item["lon"] = coords.split(",", 1)
            item["street_address"] = address or None
            item["postcode"] = (re.search(r"\b\d{4}\b", postcode) or [None])[0]
            item["phone"] = phone or None
            item["opening_hours"] = self.parse_hours(hours)
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(lines: list[str]) -> OpeningHours:
        # "E Hënë - E Premte: 07.30:15.30", "E Shtunë: Pushim" (closed), "E Diel: 08:00-14:00"
        oh = OpeningHours()
        for line in lines:
            label, _, text = line.partition(":")
            days = DAY_LABELS.get(re.sub(r"\s+", " ", label).strip().lower())
            if days is None:
                continue
            if "pushim" in text.lower() and not TIME_RE.search(text):
                oh.set_closed(days)
                continue
            text = re.split(r"teren", text, flags=re.IGNORECASE)[0]  # "Teren ora ..." = rounds, not counter
            times = [f"{h}:{m}" for h, m in TIME_RE.findall(text) if int(h) <= 24 and int(m) < 60]
            if not times or len(times) % 2:
                continue
            for day in days:
                for start, end in zip(times[::2], times[1::2]):
                    oh.add_range(day, start, end)
        return oh
