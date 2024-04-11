import json
import re

from scrapy import Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class DozApotekSE(Spider):
    name = "doz_apotek_se"
    item_attributes = {"brand": "Doz Apotek", "brand_wikidata": "Q10475311"}
    start_urls = ["https://dozapotek.se/hitta-apotek"]

    def parse(self, response, **kwargs):
        for location in json.loads(re.search(r"let cepdTechLocalStoreList = (\[.+\]);", response.text).group(1)):
            item = Feature()
            item["ref"] = location["local_store_id"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["name"] = location["name"]
            item["street_address"] = location["address"]
            item["city"] = location["post_city"]
            item["postcode"] = location["postcode"]
            item["website"] = response.urljoin(location["page_path"])
            item["extras"]["check_date"] = location["updated_at"]

            for contact in location["contact_list"]:
                self.crawler.stats.inc_value("x/{}".format(contact["type_name"]))
                if contact["type_name"] == "telefon":
                    item["phone"] = contact["value"]

            item["opening_hours"] = OpeningHours()
            for rule in location["working_hours_for_day_list"]:
                for times in rule["working_hours_record_list"]:
                    item["opening_hours"].add_range(
                        DAYS[rule["day_id"] - 1], times["start_time_24h"], times["end_time_24h"]
                    )

            yield item
