import re

from scrapy import Spider

from locations.items import Feature


class VivacomBGSpider(Spider):
    name = "vivacom_bg"
    item_attributes = {
        "brand": "Vivacom",
        "brand_wikidata": "Q7937522",
        "country": "BG",
    }
    start_urls = ["https://www.vivacom.bg/bg/stores/xhr?method=getJSON"]

    def parse(self, response):
        for store in response.json():
            if "partners" in store["store_img"]:
                continue

            item = Feature()

            item["ref"] = store["store_id"]
            item["lat"], item["lon"] = store["latlng"].split(",")
            item["name"] = store["store_name"]
            item["phone"] = store["store_phone"]

            opening_hours = (
                store["store_time"]
                .strip()
                .replace("почивен ден", "off")
                .replace("пон.", "Mo")
                .replace("пт.", "Fr")
                .replace("пет.", "Fr")
                .replace("съб.", "Sa")
                .replace("съб", "Sa")
                .replace("нед.", "Su")
                .replace("нд.", "Su")
                .replace("  ", " ")
            )
            oh = []
            for rule in re.findall(
                r"(\w{2})\s?-?\s?(\w{2})?:?\s?(\d{2}(\.|:)\d{2})\s?-\s?(\d{2}(\.|:)\d{2})",
                opening_hours,
            ):
                start_day, end_day, start_time, _, end_time, _ = rule
                start_time = start_time.replace(".", ":")
                end_time = end_time.replace(".", ":")

                if end_day:
                    oh.append(f"{start_day}-{end_day} {start_time}-{end_time}")
                else:
                    oh.append(f"{start_day} {start_time}-{end_time}")

            item["opening_hours"] = "; ".join(oh)

            yield item
