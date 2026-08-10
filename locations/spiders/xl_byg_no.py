import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class XlBygNOSpider(scrapy.Spider):
    name = "xl_byg_no"
    item_attributes = {"brand": "XL-Bygg", "brand_wikidata": "Q10720798"}
    start_urls = [
        "https://m6nlvvfa.apicdn.sanity.io/v2024-12-10/data/query/xlbygg-production?query=*%5B_type+%3D%3D+%22store%22+%26%26+%21defined%28properties%5Blower%28key%29+%3D%3D+%22web%22+%26%26+lower%28value%29+%3D%3D+%22byggeriet%22%5D%5B0%5D%29+%26%26+isActive+%21%3D+false%5D%5B0..%24take%5D%7B%0A_id%2C%0Aname%2C%0Aaddress%2C%0AphoneNumber%2C%0Aemail%2C%0A%22slug%22%3A+slug.current%2C%0Ageo%2C%0AmondayOpeningHours%2C%0AtuesdayOpeningHours%2C%0AimageUrl%2C%0AwednesdayOpeningHours%2C%0AthursdayOpeningHours%2C%0AfridayOpeningHours%2C%0AsaturdayOpeningHours%2C%0AsundayOpeningHours%2C%0A%7D+%7C+order%28name+asc%29&%24query=%22%22&%24storeId=%22%22&%24take=150&returnQuery=false&perspective=published"
    ]

    def parse(self, response, **kwargs):
        for store in response.json().get("result"):
            item = DictParser.parse(store)
            item["ref"] = store.get("_id")
            item["website"] = f'https://www.xl-bygg.no/butikker/{store.get("slug")}'
            item["image"] = store.get("imageUrl")
            item["branch"] = item.pop("name").removeprefix("XL-BYGG ").strip().capitalize()
            item.pop("state")  # State in source data is just their "store region"

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                timing = store.get(f"{day.lower()}OpeningHours", {})
                if timing.get("isOpen"):
                    item["opening_hours"].add_range(day, timing["openFrom"], timing["openTo"], time_format="%H:%M:%S")
            yield item
