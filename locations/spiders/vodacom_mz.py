from scrapy import Request
from scrapy.http import JsonRequest

from locations.hours import DAYS_3_LETTERS, DAYS_WEEKDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class VodacomMZSpider(JSONBlobSpider):
    name = "vodacom_mz"
    item_attributes = item_attributes = {
        "brand": "Vodacom Moçambique",
        "brand_wikidata": "Q130477552",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }
    start_urls = ["https://www.vm.co.mz/lojas"]
    locations_key = "data"

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_provinces)

    def parse_provinces(self, response):
        for province in response.xpath('.//select[@data-testid="select-province"]/option'):
            province_id = province.xpath("@value").get()
            province_name = province.xpath("text()").get()
            yield JsonRequest(
                url=f"https://website-api.vm.co.mz/api/shops?populate[0]=working_days&populate[1]=sat&populate[2]=sun&filters[province]={province_id}",
                callback=self.parse,
                meta={"province": province_name},
            )

    def pre_process_data(self, feature: dict):
        for key, value in feature["attributes"].items():
            feature[key] = value

    def post_process_item(self, item, response, location):
        item["state"] = response.meta["province"]
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")

        item["opening_hours"] = OpeningHours()
        for day in location["working_days"]:
            if day["is_open"]:
                item["opening_hours"].add_ranges_from_string(
                    f'{day["working_days"]} {day["open"].replace(":00.000", "")}-{day["close"].replace(":00.000", "")}'
                )
            elif day["working_days"] in DAYS_3_LETTERS:
                item["opening_hours"].set_closed(day["working_days"])
            elif day["working_days"] == "Weekdays":
                for weekday in DAYS_WEEKDAY:
                    item["opening_hours"].set_closed(weekday)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/closed/failed")
        yield item
