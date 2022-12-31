import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class KiplingSpider(scrapy.Spider):
    name = "kipling"
    item_attributes = {"brand": "Kipling", "brand_wikidata": "Q6414641"}
    allowed_domains = ["kipling-usa.com"]
    start_urls = (
        "https://www.kipling-usa.com/on/demandware.store/Sites-kip-Site/default/Stores-GetNearestStores?countryCode=US&onlyCountry=true",
    )

    def parse(self, response):
        data = response.json()

        for _, store in data.items():
            if any(depart in store.get("department") for depart in ["Retail Store", "Outlet Store"]):
                item = DictParser.parse(store)
                item["ref"] = store.get("storeID")
                item["website"] = f'https://www.{self.allowed_domains[0]}/store-details?storeid={item["ref"]}'

                openHours = []
                time_format = "%I:%M %p"
                daysOFF = ["Store Closed", "Store is closed", "Black Friday", "CLOSED"]
                for row in re.split(";|\n", store.get("storeHours")):
                    if any(dayoff in row for dayoff in daysOFF):
                        continue
                    row = row.replace(".", ":")
                    daysfull = re.findall(r"[A-Za-z]+ {0,1}- {0,1}[A-Za-z]+|[A-Za-z]+", row)[0]
                    days = [day[:2] for day in daysfull.split(" - ")]
                    openHours.extend(
                        f'{DAYS[i]} {row.replace(daysfull, "").strip()}'
                        for i in range(
                            DAYS.index(days[0]),
                            DAYS.index(days[1 if len(days) == 2 else 0]) + 1,
                        )
                    )
                    time_format = "%I:%M %p" if re.findall(r" a| p", openHours[0], re.IGNORECASE) else "%I:%M%p"
                oh = OpeningHours()
                oh.from_linked_data({"openingHours": openHours}, time_format)
                item["opening_hours"] = oh.as_opening_hours()

                yield item
