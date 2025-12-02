import re

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours, sanitise_day
from locations.items import Feature


class VolksbankATSpider(scrapy.Spider):
    name = "volksbank_at"
    item_attributes = {
        "brand": "Volksbank",
        "brand_wikidata": "Q695110",
    }
    start_urls = ["https://www.volksbank.at/m101/volksbank/DownloadServlet?action=vb_finder_ajax"]
    no_refs = True

    def parse(self, response, **kwargs):
        for data in response.json()[0].get("all"):
            for store in data.get("filialen").get("all"):
                if "volksbank" in store.get("bankname").lower():
                    item = Feature()
                    item["name"] = store.get("filialname")
                    item["street_address"] = store.get("strasse")
                    item["lat"] = store.get("breitengrad")
                    item["lon"] = store.get("laengengrad")
                    item["city"] = store.get("ort")
                    item["phone"] = store.get("telefon")
                    item["postcode"] = store.get("plz")
                    item["email"] = store.get("email")
                    branch = store.get("branch").replace("internet_p_", "").strip()

                    if url := store.get("url"):
                        item["website"] = (
                            f"https://{url}/m101/volksbank/{branch}/de/filiale/{store.get('shortPath').strip()}.jsp"
                        )
                    apply_category(Categories.BANK, item)
                    apply_yes_no(Extras.ATM, item, "bankomat" in store.get("icons"))
                    item["opening_hours"] = OpeningHours()
                    for index, start_time, end_time in re.findall(
                        r"(\d):(\d+:\d+):(\d+:\d+)",
                        store.get("oeffnungszeiten"),
                    ):
                        day = sanitise_day(DAYS[int(index) - 2])
                        item["opening_hours"].add_range(day=day, open_time=start_time, close_time=end_time)

                    yield item
