from scrapy.http import Response

from locations.categories import HealthcareSpecialities, apply_healthcare_specialities
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VitusapotekNOSpider(JSONBlobSpider):
    name = "vitusapotek_no"
    item_attributes = {"brand": "Vitusapotek", "brand_wikidata": "Q17047215"}
    start_urls = ["https://www.vitusapotek.no/api/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Vitusapotek ").strip()
        item["street_address"] = item.pop("street")

        if url_path := feature.get("urlPath"):
            item["website"] = response.urljoin(url_path)

        item["opening_hours"] = OpeningHours()
        for rule in (feature.get("openingHours") or {}).get("regularHours", []):
            days = [DAYS[d - 1] for d in rule.get("days", []) if 1 <= d <= 7]
            hours = (rule.get("hours") or "").strip()
            if not days:
                continue
            if hours in ("", "-"):
                item["opening_hours"].set_closed(days)
            elif hours == "00:00 - 00:00":
                item["opening_hours"].add_days_range(days, "00:00", "24:00")
            elif "-" in hours:
                opens, _, closes = hours.partition("-")
                item["opening_hours"].add_days_range(days, opens.strip(), closes.strip())

        if any(f.get("value") == "Vaksinasjon" for f in (feature.get("features") or [])):
            apply_healthcare_specialities([HealthcareSpecialities.VACCINATION], item)

        yield item
