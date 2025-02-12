import re

from scrapy import Spider

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BeautyZoneZASpider(Spider):
    name = "beauty_zone_za"
    start_urls = ["https://beautyzone.co.za/locations/"]
    item_attributes = {
        "brand": "Beauty Zone",
        "brand_wikidata": "Q118185921",
    }
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//div[contains(@class, "column_column")]'):
            item = Feature()
            if branch_raw := location.xpath(".//h4/b/text()").get():
                branch_raw = branch_raw.strip()
            else:
                continue
            item["branch"] = branch_raw.replace("Beauty Zone ", "")
            info = location.xpath(".//div").get()
            info_lines = re.sub(r"<\/?.*?>", "\n", info).split("\n")
            info_lines = [line.strip() for line in info_lines]
            item["opening_hours"] = OpeningHours()
            if any(["Temporarily Closed" in line for line in info_lines]):
                continue
            for line in info_lines:
                if line in ["", branch_raw]:
                    continue
                phones = []
                if line.startswith("0"):
                    phones.append(re.sub(r"\w+", "", line))
                elif any([f"{day.lower()}:" in line.lower() for day in DAYS_3_LETTERS]):
                    line = re.sub(r"(\d) ", r"\1am ", line)
                    line = re.sub(r"(\d)$", r"\1pm", line)
                    item["opening_hours"].add_ranges_from_string(line)
                else:
                    item["street_address"] = clean_address(line)
            item["phone"] = "; ".join(phones)
            yield item
