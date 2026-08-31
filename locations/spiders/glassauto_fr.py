import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider

TIME_RE = re.compile(r"(\d{1,2})h(\d{2})?")

# Fallback phone number the site returns for many centres that have none of
# their own set; not branch-specific, so drop it rather than keep it.
PLACEHOLDER_PHONE = "05 53 99 99 99"


def parse_time(t: str) -> str | None:
    if m := TIME_RE.fullmatch(t.strip()):
        return f"{int(m.group(1)):02d}:{m.group(2) or '00'}"
    return None


class GlassautoFRSpider(SitemapSpider, StructuredDataSpider):
    name = "glassauto_fr"
    item_attributes = {"brand": "GlassAuto", "brand_wikidata": "Q131983594"}
    sitemap_urls = ["https://www.glassauto.fr/sitemap.default.xml"]
    sitemap_rules = [(r"/centre/", "parse_sd")]
    wanted_types = ["AutomotiveBusiness"]

    def pre_process_data(self, ld_data, **kwargs):
        # openingHours is a dict of day -> free text hours, not the string/list
        # format LinkedDataParser expects, so parse it ourselves and drop it
        # here to avoid a noisy parse failure.
        ld_data["_opening_hours_raw"] = ld_data.pop("openingHours", None)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "").removeprefix("GlassAuto ").strip()

        if raw_hours := ld_data.get("_opening_hours_raw"):
            item["opening_hours"] = self.parse_opening_hours(raw_hours)

        if item.get("phone") == PLACEHOLDER_PHONE:
            item["phone"] = None

        if item.get("image", "").endswith("/centers/default.webp"):
            item["image"] = None

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        apply_yes_no(Extras.VEHICLE_WINDSCREEN_REPLACEMENT_SERVICES, item, True)

        yield item

    def parse_opening_hours(self, raw_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, hours in raw_hours.items():
            for time_range in hours.split("/"):
                time_range = time_range.strip()
                if "-" not in time_range:
                    continue
                open_time, close_time = time_range.split("-", 1)
                if open_time := parse_time(open_time):
                    if close_time := parse_time(close_time):
                        oh.add_range(day, open_time, close_time)

        return oh
