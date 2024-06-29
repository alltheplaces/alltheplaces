import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class PocztaPolskaPLSpider(scrapy.Spider):
    name = "poczta_polska_pl"
    item_attributes = {"brand": "Poczta Polska", "brand_wikidata": "Q168833"}
    start_url = "https://www.poczta-polska.pl/wp-content/plugins/pp-poiloader/find-markers.php"

    formdata = {
        "tab": "tabPostOffice",
        "lng": "19",
        "lat": "52",
        "province": "0",
        "district": "0",
        "ppmapBox_Days": "dni robocze",
    }

    def start_requests(self):
        yield scrapy.FormRequest(
            url=self.start_url,
            method="POST",
            formdata=self.formdata,
            callback=self.parse,
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            item = Feature()
            item["ref"] = location.get("pni")
            item["name"] = location.get("name")
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            # Todo: More data avaiale at https://www.poczta-polska.pl/wp-content/plugins/pp-poiloader/point-info.php && payload: {pointid: xyz}
            #           don't know how to make that request and extract data
            apply_category(Categories.POST_OFFICE, item)
            yield item
