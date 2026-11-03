import re

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.hours import DAYS_RO, OpeningHours
from locations.storefinders.elfsight import ElfsightSpider


class AnimaxROSpider(ElfsightSpider):
    name = "animax_ro"
    item_attributes = {"brand": "Animax", "brand_wikidata": "Q119440709"}
    host = "shy.elfsight.com"
    shop = "animaxro.myshopify.com"
    api_key = "73d5edfc-9672-4567-b102-02ef8265ef7e"
    no_refs = True

    def post_process_item(self, item, response, location):
        item["street_address"] = location.pop("position")
        item["branch"] = item.pop("name")
        text = "\n".join(Selector(text=location["infoDescription"]).xpath("//text()").getall()).replace("\xa0", " ")
        text = re.sub(r"(\d+:\d\d) AM\s*-\s*((?:1[3-9]|2[0-3]):\d\d) PM", r"\1 - \2", text)
        if match := re.search(r"☎\s*([\d.\s]+\d)", text):
            item["phone"] = match.group(1)
        if match := re.search(r"✉\s*(\S+@\S+)", text):
            item["email"] = match.group(1)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(text, days=DAYS_RO)
        apply_category(Categories.SHOP_PET, item)
        yield item
