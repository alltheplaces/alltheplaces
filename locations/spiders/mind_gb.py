import json
import re
# from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class MindGBSpider(JSONBlobSpider):
    name = "mind_gb"
    item_attributes = {"brand": "Mind", "brand_wikidata": "Q3314763"}
    start_urls = ["https://www.mind.org.uk/mind-charity-shops/find-our-local-mind-shops/"]
    requires_proxy = True


    def parse(self, response):
        match = re.search(r"const locations = ([^\n]+)",response.text)
        data = match.group(1)[:-1]
        json_data = json.loads(data)
        for location in json_data:
            item=Feature()
            item["name"] = 'Mind Charity Shop'
            item["branch"] = location["name"].replace(" shop","").replace(" Mind","").replace(" Shop","")
            item["ref"] = item["branch"]
            item["lat"],item["lon"] = location["position"]["lat"],location["position"]["lng"]
            temp = location["content"].replace("\n","")
            temp = re.sub(r"</?(?:(p|ul|li|span|div))[^>]*>",",",temp).replace(",,",",")
            print(temp)
            if "Opening hours" in temp:
                result = re.search(r"Opening hours(.*),,(.*?)(?:(Phone|Email))",temp)
                hours = result.group(1)
                address = result.group(2).replace("<br />","")
                item["opening_hours"] = hours
                item["addr_full"] = address
            if "Phone:" in temp:
                phone = re.search(r"Phone: <a href=\"tel:([^\"]*)\"",temp).group(1)
                item["phone"] = phone
            if "Email:" in temp:
                email = re.search(r"Email: <a href=\"mailto:(.*)\"",temp).group(1)
                item["email"] = email
            yield item
