import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GrainDeMaliceFRSpider(SitemapSpider, StructuredDataSpider):
    name = "grain_de_malice_fr"
    item_attributes = {"brand": "Grain de Malice", "brand_wikidata": "Q66757157"}
    sitemap_urls = ["https://www.graindemalice.fr/fr-fr/sitemap-old-boutiques.xml"]
    sitemap_rules = [(r"^https://boutiques\.graindemalice\.fr/[^/]+/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    drop_attributes = {"image"}

    def pre_process_data(self, ld_data, **kwargs):
        raw_hours = ld_data.get("openingHours")
        if not isinstance(raw_hours, list):
            return

        opening_hours = []
        valid = True
        for schedule in raw_hours:
            if not isinstance(schedule, str):
                valid = False
                break

            for day_schedule in re.split(r"<br\s*/?>", schedule, flags=re.IGNORECASE):
                day_schedule = day_schedule.strip()
                if not day_schedule:
                    continue

                day, separator, hours = day_schedule.partition(":")
                day = day.strip()
                if not separator or day not in {"Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"}:
                    valid = False
                    break

                hours = hours.strip()
                if hours.casefold() == "fermé":
                    opening_hours.append(f"{day} closed")
                    continue

                ranges = []
                for time_range in hours.split(","):
                    match = re.fullmatch(r"\s*(\d{2})h(\d{2})\s*-\s*(\d{2})h(\d{2})\s*", time_range)
                    if not match:
                        valid = False
                        break
                    open_hour, open_minute, close_hour, close_minute = match.groups()
                    ranges.append(f"{open_hour}:{open_minute}-{close_hour}:{close_minute}")

                if not valid:
                    break
                opening_hours.append(f"{day} {','.join(ranges)}")

            if not valid:
                break

        if valid:
            ld_data["openingHours"] = opening_hours
        else:
            self.logger.warning("Unable to normalize opening hours for %s", ld_data.get("name"))
            ld_data.pop("openingHours", None)

    def post_process_item(self, item, response, ld_data, **kwargs):
        match = re.fullmatch(r"https://www\.graindemalice\.fr/fr-fr/magasins/(\d+)/?", response.url)
        if not match:
            self.logger.warning(
                "Ignoring legacy store page that did not resolve to a current store page: %s", response.url
            )
            return

        item["ref"] = match.group(1)
        yield item
