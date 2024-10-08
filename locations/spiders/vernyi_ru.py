from chompjs import chompjs

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class VernyiRUSpider(JSONBlobSpider):
    name = "vernyi_ru"
    start_urls = ["https://www.verno-info.ru/shops"]
    item_attributes = {"brand_wikidata": "Q110037370"}

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[@type="text/javascript" and contains(text(), "var shops =")]').get()
        )

    def post_process_item(self, item, response, location):
        if location.get("will_open_soon") == 1:
            return
        self.parse_hours(item, location)
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item

    def parse_hours(self, item, poi):
        time_weekdays = poi.get("worktime_weekdays")
        time_weekends = poi.get("worktime_weekends")
        if time_weekdays and time_weekends:
            try:
                oh = OpeningHours()
                for time, days in [(time_weekdays, DAYS_WEEKDAY), (time_weekends, DAYS_WEEKEND)]:
                    if not time:
                        continue
                    if time.lower() == "круглосуточно":
                        oh.add_days_range(days, "00:00", "23:59")
                        continue
                    open, close = time.replace(" ", "").replace("—", "-").replace(".", ":").split("-")
                    oh.add_days_range(days, open, close)
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Couldn't parse opening hours: {time_weekdays} {time_weekends}, {e}")
