import chompjs
from typing import AsyncIterator
from scrapy import Request
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.hours import DAYS, OpeningHours
from datetime import datetime


class PatriziaPepeSpider(JSONBlobSpider):
    name = "patrizia_pepe"
    item_attributes = {
        "brand": "Patrizia Pepe",
        "brand_wikidata": "Q3897831",
    }
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}
        
    start_url = "https://www.patriziapepe.com/it/en/stores"
    json_url = "https://www.patriziapepe.com/on/demandware.store/Sites-patriziapepe_EU-Site/en_IT/Stores-All"



    async def start(self) -> AsyncIterator[Request | JsonRequest]:
        yield Request(
            self.start_url,
            callback=self.parse_stores_page,
        )
    
    def parse_stores_page(self, response: TextResponse):
        csrf_token = response.css(
            'form[name="storelocator__all-stores"] '
            'input[name="csrf_token"]::attr(value)'
        ).get()

        if not csrf_token:
            raise ValueError("Could not extract Patrizia Pepe CSRF token")

        yield JsonRequest(
            self.json_url+"?csrf_token="+csrf_token,
            callback=self.parse,
        )

    @staticmethod
    def normalize_time(value):
        if not value:
            return value

        value = value.strip()

        for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
            try:
                return datetime.strptime(value, fmt).strftime("%H:%M")
            except ValueError:
                pass

        return value

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name", "")
        slug = item.pop("website")
        if slug:
            item["website"] = "https://www.patriziapepe.com" + slug
              
        
        item["opening_hours"] = OpeningHours()
        hours = location.get("hours")
        if hours:

            day_hours = {
                "Mo": ("monStart", "monEnd"),
                "Tu": ("tueStart", "tueEnd"),
                "We": ("wedStart", "wedEnd"),
                "Th": ("thuStart", "thuEnd"),
                "Fr": ("friStart", "friEnd"),
                "Sa": ("satStart", "satEnd"),
                "Su": ("sunStart", "sunEnd"),
            }
            for day, (start_key, end_key) in day_hours.items():
                start = hours.get(start_key)
                end = hours.get(end_key)

                print(day,start,"e", end)
                if start == "closed" or end == "closed":
                    item["opening_hours"].set_closed(day)
                elif start and end:
                    item["opening_hours"].add_range(day, self.normalize_time(start.replace(".",":")), self.normalize_time(end.replace(".",":")))

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
