import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class ColdwellBankerUSSpider(SitemapSpider):
    name = "coldwell_banker_us"
    item_attributes = {"brand": "Coldwell Banker", "brand_wikidata": "Q738853"}
    sitemap_urls = ["https://www.coldwellbanker.com/robots.txt"]
    sitemap_follow = ["offices"]
    sitemap_rules = [(r"/oid-", "parse")]

    def parse(self, response, **kwargs):
        office = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"].get(
            "detail", {}
        )
        if office.get("addresses"):
            office.update(office.pop("addresses")[0])
        office.update(office.pop("geoLocation"))
        item = DictParser.parse(office)
        item["ref"] = office.get("officeMasterId")
        item["branch"] = office.get("officeName").replace("Coldwell Banker ", "")
        item["street_address"] = item.pop("addr_full") if item.get("addr_full") else item.get("street_address")
        item["website"] = response.url
        item["phone"] = office.get("businessPhoneNumber")
        item["email"] = office.get("businessEmail")
        item["extras"]["fax"] = office.get("faxNumber")
        yield item
