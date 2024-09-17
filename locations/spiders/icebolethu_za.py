from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature

ICEBOLETHU_CATEGORIES = {"branches": Categories.SHOP_FUNERAL_DIRECTORS, "mortuaryinformation": Categories.MORTUARY}


class IcebolethuZASpider(Spider):
    name = "icebolethu_za"
    item_attributes = {"brand": "Icebolethu Funerals", "brand_wikidata": "Q122594408"}
    allowed_domains = ["www.icebolethugroup.co.za"]
    start_urls = ["https://www.icebolethugroup.co.za/contact/"]
    no_refs = True

    def parse(self, response):
        for id in ICEBOLETHU_CATEGORIES:
            for location in response.xpath(f'//*[@id="{id}"]//*[@class="question"]'):
                item = Feature()
                name_or_branch = location.xpath('.//*[@class="title wpb_toggle"]/text()').get()
                if id == "branches":
                    item["branch"] = name_or_branch
                else:
                    item["name"] = name_or_branch

                info = [
                    detail.strip()
                    for detail in location.xpath('.//*[@class="wpb_toggle_content answer"]/p/text()').getall()
                    if detail.strip() != ""
                ]

                for detail in info:
                    if detail[0] == "0":
                        item["phone"] = detail
                    else:
                        item["street_address"] = detail

                # Some short maps.app.goo.gl links which can't be extracted from
                try:
                    item["lat"], item["lon"] = url_to_coords(
                        location.xpath('.//a[contains(@href, "google.com/maps")]/@href').get()
                    )
                except:
                    pass

                apply_category(ICEBOLETHU_CATEGORIES[id], item)

                yield item
