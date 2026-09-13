import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

DAY_FR = {
    "Lundi": "Mo",
    "Mardi": "Tu",
    "Mercredi": "We",
    "Jeudi": "Th",
    "Vendredi": "Fr",
    "Samedi": "Sa",
    "Dimanche": "Su",
}

HOURS_RE = re.compile(
    rf"({'|'.join(DAY_FR)})\s*((?:\d{{1,2}}h\d{{2}}\s*-\s*)*\d{{1,2}}h\d{{2}}|Ferm[ée])",
    re.IGNORECASE,
)


class VAndBFRSpider(SitemapSpider, StructuredDataSpider):
    name = "v_and_b_fr"
    item_attributes = {"brand": "V and B", "brand_wikidata": "Q100706329"}
    sitemap_urls = ["https://www.vandb.fr/sitemap.xml"]
    sitemap_rules = [(r"https\:\/\/www\.vandb\.fr\/nos-magasins\/.+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_ALCOHOL, item)
        item["opening_hours"] = self.parse_opening_hours(response)
        yield item

    def parse_opening_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()

        text = " ".join(response.xpath("//text()").getall()).replace("\xa0", " ")
        text = re.sub(r"[–—]", "-", text)
        text = re.sub(r"\s+", " ", text)

        if not (matches := HOURS_RE.findall(text)):
            self.crawler.stats.inc_value("atp/v_and_b_fr/no_hours_found")
            return oh

        for day_fr, hours_str in matches:
            if hours_str.lower().startswith("ferm"):
                continue

            times = [t.replace("h", ":") for t in re.findall(r"\d{1,2}h\d{2}", hours_str)]
            for i in range(0, len(times), 2):
                if i + 1 < len(times):
                    oh.add_range(DAY_FR[day_fr.capitalize()], times[i], times[i + 1], time_format="%H:%M")

        return oh
