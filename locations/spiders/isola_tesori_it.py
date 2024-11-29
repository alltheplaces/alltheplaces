from unidecode import unidecode

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


def clean_strings(iterator):
    return list(filter(bool, map(str.lower, map(str.strip, iterator))))


class IsolaTesoriITSpider(JSONBlobSpider):
    name = "isola_tesori_it"
    item_attributes = {"brand": "L'Isola dei Tesori", "brand_wikidata": "Q108578003"}
    start_urls = ["https://www.isoladeitesori.it/on/demandware.store/Sites-idt-it-Site/it_IT/Stores-FindStores"]
    locations_key = "stores"

    def post_process_item(self, item, response, location):
        item["branch"] = item["name"]
        item["name"] = self.item_attributes["brand"]
        item["website"] = f"https://www.isoladeitesori.it/store/{item['website']}.html"

        apply_category(Categories.SHOP_PET, item)

        yield response.follow(item["website"], cb_kwargs={"item": item}, callback=self.parse_store_oph)

    def parse_store_oph(self, response, item):
        hours = clean_strings(unidecode(s) for s in response.css(".store-hours td::text").getall())
        oh = OpeningHours()
        for day, hour in zip(hours[0::2], hours[1::2]):
            oh.add_ranges_from_string(
                f"{day} {hour}",
                days=DAYS_IT,
                named_day_ranges=NAMED_DAY_RANGES_IT,
                named_times=NAMED_TIMES_IT,
                closed=CLOSED_IT,
            )
        if oh:
            item["opening_hours"] = oh

        yield item
