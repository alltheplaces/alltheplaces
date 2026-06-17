import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class DimeglioITSpider(Spider):
    name = "dimeglio_it"
    item_attributes = {"brand": "DiMeglio Supermercati"}
    start_urls = ["https://www.dimegliosupermercati.com/punti-vendita-dimeglio/"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response):
        # Extract store URLs from the clickable table rows, used as refs.
        store_urls = response.xpath("//td[contains(@onclick, 'document.location.href')]/@onclick").getall()
        refs = []
        for onclick in store_urls:
            if m := re.search(r"'(https://[^']+)'", onclick):
                url = m.group(1).rstrip("/")
                refs.append(url.split("/")[-1])

        # Extract gMap markers from the embedded JavaScript.
        gmap_js = response.xpath('//script[contains(text(), "gMap")][contains(text(), "latitude")]/text()').get("")
        marker_pattern = r"\{latitude: ([0-9.-]+),longitude: ([0-9.-]+),html: \"(.*?)\",\}"
        markers = re.findall(marker_pattern, gmap_js, re.DOTALL)

        for i, (lat, lon, html_content) in enumerate(markers):
            # Extract branch name (strip HTML and brand prefix).
            name_match = re.search(r"<b>(.*?)</b>", html_content)
            if not name_match:
                continue
            branch = re.sub(r"<[^>]+>", "", name_match.group(1)).strip()
            branch = re.sub(r"^Supermercato Di Meglio\s+", "", branch).strip()

            # Extract street address.
            addr_match = re.search(r"Indirizzo:\s*(.*?)(?:<br|Telefono|\[)", html_content, re.DOTALL)
            addr_raw = re.sub(r"<[^>]+>", "", addr_match.group(1)).strip().rstrip(",").strip() if addr_match else ""

            # Parse city and state from address patterns like "Via X 1, City(ST)" or "Via X | City(ST)".
            city = state = ""
            street = addr_raw
            city_match = re.search(r"[|,]\s*([^|(,]+)\(([A-Z]{2})\)", addr_raw)
            if city_match:
                city = city_match.group(1).strip()
                state = city_match.group(2).strip()
                street = addr_raw[: city_match.start()].strip().rstrip(",| ").strip()

            # Extract phone.
            phone_match = re.search(r"Telefono:\s*([^<\[\\]+)", html_content)
            phone = phone_match.group(1).strip() if phone_match else ""
            # Normalise Italian phone format "0185/232064" → "+390185232064".
            if phone:
                phone = re.sub(r"\s+", "", phone)

            # Extract opening hours text.
            hours_match = re.search(r"Orari:\s*(.*?)(?:\",|$)", html_content, re.DOTALL)
            oh = OpeningHours()
            if hours_match:
                hours_text = re.sub(r"<[^>]+>", " ", hours_match.group(1)).strip()
                hours_text = re.sub(r"\s+", " ", hours_text)
                oh.add_ranges_from_string(
                    hours_text,
                    days=DAYS_IT,
                    named_day_ranges=NAMED_DAY_RANGES_IT,
                    named_times=NAMED_TIMES_IT,
                    delimiters=DELIMITERS_IT,
                    closed=CLOSED_IT,
                )

            item = Feature(
                ref=refs[i] if i < len(refs) else f"dimeglio-{i}",
                branch=branch,
                street_address=street,
                city=city,
                state=state,
                country="IT",
                phone=phone or None,
                lat=float(lat),
                lon=float(lon),
                opening_hours=oh,
                website=f"https://www.dimegliosupermercati.com/{refs[i]}/" if i < len(refs) else None,
            )
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
