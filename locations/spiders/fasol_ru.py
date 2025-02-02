import chompjs

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class FasolRUSpider(JSONBlobSpider):
    name = "fasol_ru"
    item_attributes = {
        "brand": "Фасоль",
        "brand_wikidata": "Q132005368",
    }
    start_urls = ["https://myfasol.ru/stores/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath("//div[@data-slide-id='map']/script/text()").get())

    def post_process_item(self, item, response, location):
        item.pop("city")

        try:
            work_from, work_till = location.get("work_from"), location.get("work_till")
            if work_from and work_till:
                oh = OpeningHours()
                oh.add_days_range(DAYS, work_from, work_till)
                item["opening_hours"] = oh
        except ValueError as e:
            self.logger.warning(f"Error parsing hours: {e}")
            self.crawler.stats.inc_value(f"atp/hours/failed")

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
