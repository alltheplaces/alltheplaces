import re
from typing import Iterable

import phonenumbers
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TerveystaloFISpider(SitemapSpider, StructuredDataSpider):
    name = "terveystalo_fi"
    # Brand pending NSI brand entry (osmlab#12971); operator entry already live.
    item_attributes = {
        "brand": "Terveystalo",
        "name": "Terveystalo",
        "operator": "Terveystalo",
        "operator_wikidata": "Q11897034",
    }
    sitemap_urls = ["https://www.terveystalo.com/sitemap.xml"]
    # Two slugs break the prefix convention (partner venue / short name).
    sitemap_rules = [
        (r"/fi/toimipaikat/(terveystalo-[^/]+)/?$", "parse"),
        (r"/fi/toimipaikat/(--ikaalinen-e-avenue)/?$", "parse"),
        (r"/fi/toimipaikat/(tikkurila-varitehtaankatu)/?$", "parse"),
    ]
    wanted_types = ["MedicalClinic"]
    # Page tel:/social/og:image are shared brand-level assets.
    search_for_phone = False
    search_for_facebook = False
    search_for_twitter = False
    search_for_image = False
    # No hours: LD carries none and page prose mixes per-department hours with by-appointment tokens.

    @staticmethod
    def _is_hotline(value: str) -> bool:
        # Null shared 0900 30 000 / 030 6000 runs (other 0900 numbers never contain them) and not-for-clients lines.
        digits = re.sub(r"[\s\-*\u200b]", "", value)
        if "090030000" in digits or "0306000" in digits:
            return True
        low = value.casefold()
        return "ei asiakkaille" in low or "sisäiseen käyttöön" in low

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        # Drop shared-hotline entries so parse_ld keeps the per-unit number.
        tel = ld_data.get("telephone")
        if isinstance(tel, str):
            tel = [tel]
        if isinstance(tel, list):
            kept = [self._first_phone(t) for t in tel if isinstance(t, str) and t and not self._is_hotline(t)]
            ld_data["telephone"] = kept or None

    @staticmethod
    def _first_phone(value: str) -> str:
        # LD packs a sentence or several numbers into one string; keep the first real number.
        match = next(iter(phonenumbers.PhoneNumberMatcher(value, "FI")), None)
        return match.raw_string.strip() if match else value.strip()

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "Toimipaikka aukeaa" in response.text:
            # Unopened unit (only Lahti Trio, opening 11.11.2026); skip until it opens.
            self.logger.warning("Skipping unopened unit: %s", response.url)
            return
        if not item.get("street_address") and item.get("lat") in (None, 0):
            # Digital-only service: no street and no usable coords.
            self.logger.warning("Skipping digital-only unit: %s", response.url)
            return
        phone = item.get("phone") or ""
        if "@" in phone:
            # Upstream typo: an email address in the telephone field.
            if not item.get("email"):
                item["email"] = phone.strip()
            item["phone"] = None
        label = self._split_branch(item)
        if "hammas" in label or "crossdental" in label:
            apply_category(Categories.DENTIST, item)
        elif "fysio" in label:
            apply_category(Categories.PHYSIOTHERAPIST, item)
        elif "kuntoutus" in label:
            apply_category(Categories.REHABILITATION, item)
        else:
            apply_category(Categories.CLINIC, item)
        yield item

    def _split_branch(self, item: Feature) -> str:
        # Brand is the feature name; the remaining per-location text is the branch.
        name = (item.get("name") or "").strip()
        low = name.casefold()
        if low == "terveystalo" or low.startswith("terveystalo "):
            branch = name[len("Terveystalo") :].strip()
        else:
            branch = name
        if branch:
            item.pop("name", None)
            item["branch"] = branch
            return branch.casefold()
        return low
