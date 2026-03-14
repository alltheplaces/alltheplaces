from scrapy import Spider

from locations.items import Feature


class FostersFreezeUSSpider(Spider):
    name = "fosters_freeze_us"
    item_attributes = {"brand": "Fosters Freeze", "brand_wikidata": "Q5473851"}
    start_urls = ["https://www.fostersfreeze.com/locations/"]
    no_refs = True

    def parse(self, response):
        for location in response.xpath("//mappress-map/poi"):
            lat, lon = location.xpath("@point").get().split(",")
            yield Feature(
                addr_full=location.xpath("@address").get(),
                lat=lat,
                lon=lon,
                branch=location.xpath("@title").get().removeprefix("Fosters Freeze, "),
            )
