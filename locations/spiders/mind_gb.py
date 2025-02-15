import json
import re

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MindGBSpider(JSONBlobSpider):
    name = "mind_gb"
    item_attributes = {"brand": "Mind", "brand_wikidata": "Q3314763"}
    start_urls = ["https://www.mind.org.uk/mind-charity-shops/find-our-local-mind-shops/"]
    requires_proxy = True

    def parse(self, response):
        match = re.search(r"const locations = ([^\n]+)", response.text)
        data = match.group(1)[:-2]
        json_data = json.loads(data)
        for location in json_data:
            item = Feature()
            item["name"] = "Mind Charity Shop"
            item["branch"] = location["name"].replace(" shop", "").replace(" Mind", "").replace(" Shop", "")
            item["ref"] = item["branch"]
            item["lat"], item["lon"] = location["position"]["lat"], location["position"]["lng"]
            temp = location["content"].replace("\n", "")
            temp = re.sub(r"</?(?:(p|ul|li|span|div))[^>]*>", ",", temp).replace(",,", ",")
            if "Opening hours" in temp:
                item["opening_hours"] = OpeningHours()
                result = re.search(r"Opening hours(.*),,(.*?)(?:(Phone|Email))", temp)
                hours = result.group(1)
                #Example ,Monday to Saturday 9:00am - 4:00pm,Sunday 10:00am - 4:00pm
                hours_split=hours.replace("&nbsp;","").split(",")
                for hours_range in hours_split:
                    item["opening_hours"].add_ranges_from_string(hours_range)
                address = result.group(2).replace("<br />", "")
                item["opening_hours"] = hours
                item["addr_full"] = address
            if "Phone:" in temp:
                phone = re.search(r"Phone: <a href=\"tel:([^\"]*)\"", temp).group(1)
                item["phone"] = phone
            if "Email:" in temp:
                email = re.search(r"Email: <a href=\"mailto:(.*)\"", temp).group(1)
                item["email"] = email
            yield item
