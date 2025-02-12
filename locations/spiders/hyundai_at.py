import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HyundaiATSpider(scrapy.Spider):
    name = "hyundai_at"
    item_attributes = {"brand": "Hyundai", "brand_wikidata": "Q55931"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.hyundai.at/umbraco/Surface/PartnerFinden/GetMapMarkers?_=1692350353389"]
    handle_httpstatus_list = [500]

    def parse(self, response, **kwargs):
        for dealer in response.json():
            item = DictParser.parse(dealer)
            item["name"] = dealer.get("DisplayName")
            item["postcode"] = dealer.get("Plz")
            item["street_address"] = dealer.get("Strasse")
            item["city"] = dealer.get("Ort")
            item["state"] = dealer.get("Bundesland")

            if dealer.get("Verkauf"):
                apply_category(Categories.SHOP_CAR, item)
            else:
                apply_category(Categories.SHOP_CAR_REPAIR, item)

            if dealer.get("Werkstatt"):
                item["extras"]["service"] = "dealer;repair"

            yield scrapy.Request(
                url=f"https://www.hyundai.at/umbraco/Surface/PartnerFinden/PartnerDetails?motiondataId={dealer['MotiondataId']}&isSelectable=false&_=1692350353390",
                callback=self.parse_more_details,
                cb_kwargs=dict(item=item),
            )

    def parse_more_details(self, response, item):
        if response.status == 500:
            yield item
        else:
            item["email"] = response.xpath('//a[contains(@href, "mailto")]/@href').get().replace("mailto:", "")
            item["phone"] = response.xpath('//a[contains(@href, "tel")]/@href').get().replace("tel:", "")
            item["extras"]["website_2"] = response.xpath('//a[contains(text(), "Website")]/@href').get()
            yield item
