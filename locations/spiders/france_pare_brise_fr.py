import json
import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature, SocialMedia, set_social_media
from locations.structured_data_spider import clean_instagram


class FrancePareBriseFRSpider(SitemapSpider):
    name = "france_pare_brise_fr"
    item_attributes = {"brand": "France Pare-Brise", "brand_wikidata": "Q63335107", "name": "France Pare-Brise"}
    sitemap_urls = ["https://centre.franceparebrise.fr/sitemap.xml"]
    sitemap_rules = [(r"^https://centre\.franceparebrise\.fr/reparation-pare-brise/[^/]+/[^/]+/[^/]+/[^/]+$", "parse")]
    LOCATED_IN_MAPPINGS = [
        (["Euromaster"], {"brand": "Euromaster", "brand_wikidata": "Q3060668"}),
        (["Profil Plus"], {"brand": "Profil Plus", "brand_wikidata": "Q115927114"}),
        (["First Stop", "Firststop"], {"brand": "First Stop", "brand_wikidata": "Q3072965"}),
        (["Eurotyre"], {"brand": "Eurotyre", "brand_wikidata": "Q3060871"}),
        (["Feu Vert"], {"brand": "Feu Vert", "brand_wikidata": "Q3070922"}),
        (["Eurorepar", "Euro Repar"], {"brand": "Eurorepar", "brand_wikidata": "Q117873546"}),
        (["Top Garage"], {"brand": "Top Garage", "brand_wikidata": "Q117602800"}),
        (["Midas"], {"brand": "Midas", "brand_wikidata": "Q3312613"}),
        (["BestDrive"], {"brand": "BestDrive", "brand_wikidata": "Q63057183"}),
        (["Vulco"], {"brand": "Vulco", "brand_wikidata": "Q80184403"}),
        (["Motrio"], {"brand": "Motrio", "brand_wikidata": "Q6918585"}),
        (["E.Leclerc"], {"brand": "E.Leclerc", "brand_wikidata": "Q1273376"}),
        (["Intermarché"], {"brand": "Intermarché", "brand_wikidata": "Q3153200"}),
        (["AD Garage"], {"brand": "AD", "brand_wikidata": "Q108753388"}),
        (["ADA"], {"brand": "ADA", "brand_wikidata": "Q57313774"}),
        (["Weldom"], {"brand": "Weldom", "brand_wikidata": "Q16683226"}),
        (["Komilfo"], {"brand": "Komilfo", "brand_wikidata": "Q108870467"}),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The JSON-LD keeps only the last interval of each day, so read the Yext document instead.
        location = json.loads(
            unquote(
                response.xpath('//script[@type="module"]/text()').re_first(
                    r"JSON\.parse\(decodeURIComponent\(\"(.+)\"\)\)", default=""
                )
            )
        )["document"]
        # Skip unfinished entities without a label (seen: a duplicate of a published centre).
        if not location.get("c_fPBValueForSlug"):
            self.crawler.stats.inc_value(f"atp/{self.name}/skipped_no_label")
            return

        item = DictParser.parse(location)
        item["ref"] = location["id"]
        item["website"] = response.url
        item["email"] = (location.get("emails") or [None])[0]
        item.pop("name", None)

        # Service points hosted by another business are labelled "<town> - Chez <host>".
        branch, *host = re.split(r"(?:^|[\s-]+)chez\s+", location["c_fPBValueForSlug"], maxsplit=1, flags=re.IGNORECASE)
        item["branch"] = branch.strip(" -") or None
        if host := "".join(host).strip():
            item["located_in"], item["located_in_wikidata"] = extract_located_in(host, self.LOCATED_IN_MAPPINGS, self)
            if not item["located_in"]:
                item["located_in"] = host

        if facebook := location.get("c_facebookLink"):
            set_social_media(item, SocialMedia.FACEBOOK, facebook)
        if instagram := clean_instagram(location.get("c_instagramLink") or ""):
            set_social_media(item, SocialMedia.INSTAGRAM, instagram)

        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            rule = location.get("hours", {}).get(day) or {}
            if rule.get("isClosed"):
                oh.set_closed(day)
            for interval in rule.get("openIntervals") or []:
                oh.add_range(day, interval["start"], interval["end"])
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
