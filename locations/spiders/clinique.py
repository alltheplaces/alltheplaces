import scrapy

from locations.dict_parser import DictParser


class CliniqueSpider(scrapy.Spider):
    name = "clinique"
    item_attributes = {
        "brand": "Clinique Laboratories, LLC",
        "brand_wikidata": "Q2655764",
    }
    allowed_domains = ["clinique.com"]

    def start_requests(self):
        url = "https://www.clinique.com/rpc/jsonrpc.tmpl?dbgmethod=locator.doorsandevents"
        headers = {
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        payload = 'JSONRPC=[{"method":"locator.doorsandevents","id":4,"params":[{"fields":"DOOR_ID,+DOORNAME,+EVENT_NAME,+EVENT_START_DATE,+EVENT_END_DATE,+EVENT_IMAGE,+EVENT_FEATURES,+EVENT_TIMES,+SERVICES,+STORE_HOURS,+ADDRESS,+ADDRESS2,+STATE_OR_PROVINCE,+CITY,+REGION,+COUNTRY,+ZIP_OR_POSTAL,+PHONE1,+LONGITUDE,+LATITUDE","radius":20000,"country_all":null,"latitude":40.4172871,"longitude":-82.90712300000001,"_TOKEN":"c2752ac289ca688d96f958aaf86c64986571c7a4,0c2351cf699d40814b350ba92c18a02045e9797f,1673047793"}]}]'
        yield scrapy.Request(url=url, body=payload, method="POST", headers=headers, callback=self.parse)

    def parse(self, response):
        data = response.json()[0].get("result", {}).get("value", {}).get("results", {}).items()
        for key, value in data:
            item = DictParser.parse(value)
            item["ref"] = key
            item["name"] = value.get("DOORNAME")
            item["street_address"] = item.pop("addr_full", None)
            item["postcode"] = value.get("ZIP_OR_POSTAL")
            item["state"] = value.get("STATE_OR_PROVINCE")

            yield item
