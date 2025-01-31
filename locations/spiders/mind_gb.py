import json

# from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class MindGBSpider(JSONBlobSpider):
    name = "mind_gb"
    item_attributes = {"brand": "Mind", "brand_wikidata": "Q3314763"}
    start_urls = ["https://www.mind.org.uk/mind-charity-shops/find-our-local-mind-shops/"]
    requires_proxy = True

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response):
        data = self.find_between(response.text, "const locations = ", ";").replace(";", "")
        json_data = json.loads(data)
        for location in json_data:
            item["name"] = "Mind Charity Shop"
            item["branch"] = location["name"]
            item["lat"], item["lon"] = location["position"]["lat"], location["position"]["lon"]
            # html = location["content"]
            # openinghours = html.xpath("//p/text()").getall()
            # address, phone = openinghours[-1].split("<br /><span>Phone:")
            # item["addr_full"] = address.replace("<br />", "").replace("</span><span>", ",")
            # item["phone"] = phone.xpath("//a/@href").get().replace("tel:", "")
            # openinghours.pop()
            # print(openinghours)
            yield item
