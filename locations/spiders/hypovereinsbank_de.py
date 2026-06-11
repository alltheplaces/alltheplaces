import re

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.storefinders.uberall import UberallSpider


class HypovereinsbankDESpider(UberallSpider):
    name = "hypovereinsbank_de"
    item_attributes = {"brand": "HypoVereinsbank", "brand_wikidata": "Q220189"}
    key = "QZ7auxGUWKL0MfAnUOgweafKIwrXPb"
    business_id_filter = 77215
    # Ignores:
    # 599793 - Wealth Management
    # 337143 - Unternehmenskunden (corporate clients services)
    # 337141 - Private Banking

    def post_process_item(self, item, response, location):
        item["website"] = "https://www.hypovereinsbank.de/hvb/kontaktwege/filiale#!/l/{}/{}/{}".format(
            item["city"].replace(" ", "-").lower(),
            location["streetAndNumber"].replace(" ", "-").lower(),
            location["identifier"],
        )
        name = item["name"].lower()
        note = (location.get("openingHoursNotes") or "").lower()
        item.pop("name", None)

        # Self-service-only points ("Kein Filialgeschäft. Nur SB-Geräte...") have
        # no staffed branch, so they are an ATM rather than a bank. Their
        # structured openingHours are the ATM's own hours; fall back to the
        # free-text note only when those are missing.
        if "geldautomat" in name or "sb-standort" in name or ("kein filialgeschäft" in note and "geldautomat" in note):
            apply_category(Categories.ATM, item)
            if not item["opening_hours"]:
                if atm_hours := self.parse_atm_hours(note):
                    item["opening_hours"] = atm_hours
            yield item
            return

        apply_category(Categories.BANK, item)

        if re.search(r"(keine?|ohne)\s+sb[ -]?zone", note):
            apply_yes_no(Extras.ATM, item, False, apply_positive_only=False)
        elif re.search(r"\bsb[ -]?zone\b|sb[ -]?geräte|selbstbedienung", note):
            apply_yes_no(Extras.ATM, item, True)
            if atm_hours := self.parse_atm_hours(note):
                item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()

        yield item

    def parse_atm_hours(self, note: str) -> OpeningHours | None:
        if "geschlossen" in note and "nachts" not in note:
            return None

        oh = OpeningHours()
        try:
            if re.search(r"24\s*(?:stunden|h\b)|durchgängig|ganztägig", note):
                oh.add_days_range(DAYS, "00:00", "24:00")
            elif night := re.search(
                r"nachts geschlossen von\s*\d{1,2}[:.]?\d{0,2}\s*[-–]\s*(\d{1,2})[:.]?(\d{0,2})", note
            ):
                oh.add_days_range(DAYS, "{}:{}".format(night[1].zfill(2), (night[2] or "00").zfill(2)), "24:00")
            elif span := re.search(r"(\d{1,2})[:.](\d{2})\s*(?:uhr\s*)?(?:bis|-|–|—)\s*(\d{1,2})[:.](\d{2})", note):
                days = DAYS[:6] if "samstag" in note else DAYS
                oh.add_days_range(
                    days, "{}:{}".format(span[1].zfill(2), span[2]), "{}:{}".format(span[3].zfill(2), span[4])
                )
            elif span := re.search(r"(\d{1,2})\s*(?:uhr\s*)?(?:bis|-|–|—)\s*(\d{1,2})\s*uhr", note):
                days = DAYS[:6] if "samstag" in note else DAYS
                oh.add_days_range(days, "{}:00".format(span[1].zfill(2)), "{}:00".format(span[2].zfill(2)))
            else:
                return None
        except Exception:
            self.logger.error("Failed to parse SB-Zone hours: %s", note)
            return None
        return oh
