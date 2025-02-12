from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class StarbucksJPSpider(JSONBlobSpider):
    name = "starbucks_jp"
    item_attributes = {"brand": "スターバックス", "brand_wikidata": "Q37158"}
    start_urls = ["https://store.starbucks.co.jp/store_vue/js/store.js"]
    locations_key = ["hits", "hit"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse_js,
            )

    def parse_js(self, response):
        for line in response.text.split("getPrefData()")[1].split("return $pref_data")[0].split("\n"):
            if "pref_data.push" not in line:
                continue
            prefecture = parse_js_object(line.split("pref_data.push(")[1])
            if prefecture["pref_code"] == "":
                continue
            yield JsonRequest(
                url=f"https://hn8madehag.execute-api.ap-northeast-1.amazonaws.com/prd-2019-08-21/storesearch?size=100&q.parser=structured&q=(and%20ver:10000%20record_type:1%20pref_code:{prefecture['pref_code']})&fq=(and%20data_type:%27prd%27)&sort=zip_code%20asc,store_id%20asc&start=0",
                headers={"origin": "https://store.starbucks.co.jp"},
                meta={
                    "offset": 0,
                    "prefecture": prefecture,
                },
                callback=self.parse_prefecture,
            )

    def parse_prefecture(self, response):
        yield from self.parse(response)
        if response.json()["hits"]["found"] > response.json()["hits"]["start"] + 100:
            offset = response.meta["offset"] + 100
            yield JsonRequest(
                url=f"https://hn8madehag.execute-api.ap-northeast-1.amazonaws.com/prd-2019-08-21/storesearch?size=100&q.parser=structured&q=(and%20ver:10000%20record_type:1%20pref_code:{response.meta['prefecture']['pref_code']})&fq=(and%20data_type:%27prd%27)&sort=zip_code%20asc,store_id%20asc&start={offset}",
                headers={"origin": "https://store.starbucks.co.jp"},
                meta={
                    "offset": offset,
                    "prefecture": response.meta["prefecture"],
                },
                callback=self.parse_prefecture,
            )

    def post_process_item(self, item, response, location):
        item["lat"], item["lon"] = location["fields"]["location"].split(",")

        item["branch"] = location["fields"].get("name")
        item["extras"]["branch:ja"] = location["fields"].get("name")
        item["extras"]["branch:en"] = location["fields"].get("en_name")

        item["state"] = location["fields"].get("address_1")
        item["city"] = location["fields"].get("address_2")
        item["addr_full"] = location["fields"].get("address_5")

        item["extras"]["addr:state:ja"] = item["state"]
        item["extras"]["addr:city:ja"] = item["city"]
        item["extras"]["addr:full:ja"] = item["addr_full"]

        item["extras"]["addr:state:en"] = location["fields"].get("en_address_1")
        item["extras"]["addr:city:en"] = location["fields"].get("en_address_2")
        item["extras"]["addr:full:en"] = location["fields"].get("en_address_5")

        item["website"] = f"https://store.starbucks.co.jp/detail-{location['fields']['store_id']}/"

        item["opening_hours"] = OpeningHours()
        for day in DAYS_3_LETTERS:
            open_time = location["fields"].get(f"{day.lower()}_open")
            close_time = location["fields"].get(f"{day.lower()}_close")
            if close_time == "25:00":
                close_time = "01:00"
            if open_time is None and close_time is None:
                item["opening_hours"].set_closed(day)
            try:
                item["opening_hours"].add_range(day, open_time, close_time)
            except ValueError:
                self.crawler.stats.inc_value(
                    f"atp/{self.name}/hours/failed/open/" + location["fields"].get(f"{day.lower()}_open")
                )
                self.crawler.stats.inc_value(
                    f"atp/{self.name}/hours/failed/close/" + location["fields"].get(f"{day.lower()}_close")
                )

        apply_yes_no(Extras.WIFI, item, location["fields"].get("public_wireless_service_flg") == "1")

        yield item
