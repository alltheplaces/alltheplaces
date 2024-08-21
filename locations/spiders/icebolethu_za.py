from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.settings import ITEM_PIPELINES

ICEBOLETHU_CATEGORIES = {"branches": Categories.SHOP_FUNERAL_DIRECTORS, "mortuaryinformation": Categories.MORTUARY}


class IcebolethuZASpider(Spider):
    name = "icebolethu_za"
    item_attributes = {"brand": "Icebolethu Funerals", "brand_wikidata": "Q122594408"}
    allowed_domains = ["www.icebolethugroup.co.za"]
    start_urls = ["https://www.icebolethugroup.co.za/contact/"]
    custom_settings = {
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None}
    }
    no_refs = True

    def parse(self, response):
        for id in ICEBOLETHU_CATEGORIES:
            for location in response.xpath(f'//*[@id="{id}"]//*[@class="question"]'):
                properties = {
                    "name": location.xpath('.//*[@class="title wpb_toggle"]/text()').get(),
                    "phone": location.xpath('.//*[@class="wpb_toggle_content answer"]/p/text()').get(),
                }

                info = location.xpath('string(.//*[@class="wpb_toggle_content answer"])').get().split("\n")

                # Free text, so typos mean this phrase may not be present
                try:
                    address_lines = info[1 : info.index("Open location in Google maps.")]
                except:
                    pass
                properties["street_address"] = " ".join(address_lines).lstrip("Address:").strip()

                # Some short maps.app.goo.gl links which can't be extracted from
                try:
                    properties["lat"], properties["lon"] = url_to_coords(
                        location.xpath('.//a[contains(@href, "google.com/maps")]/@href').get()
                    )
                except:
                    pass

                apply_category(ICEBOLETHU_CATEGORIES[id], properties)

                yield Feature(**properties)
