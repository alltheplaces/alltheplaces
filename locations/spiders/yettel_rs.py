import scrapy


class YettelRSSpider(scrapy.Spider):
    name = "yettel_rs"
    item_attributes = {
        "brand": "Yettel",
        "brand_wikidata": "Q1780171",
        "country": "RS",
    }

    def start_requests(self):
        url = "https://www.yettel.rs/stores/latlong/"
        yield scrapy.http.FormRequest(url=url, formdata={"initial": "true"}, method="POST")

    def parse(self, response):
        for index, store in enumerate(response.json()["data"]["stores"]):
            item["lat"] = store["lat"]
            item["lon"] = store["lng"]

            item["city"] = store["city"]
            item["postal_code"] = store["post_number"]
            item["street_address"] = store["address"]

            oh = opening_hours()

            for wh in store["workingHoursFormated"]:
                if wh.day == "Ponedeljak":
                    oh.addRange("Mo", wh.startTime, wh.endTime)
                if wh.day == "Utorak":
                    oh.addRange("Tu", wh.startTime, wh.endTime)
                if wh.day == "Sreda":
                    oh.addRange("We", wh.startTime, wh.endTime)
                if wh.day == "Četvrtak":
                    oh.addRange("Th", wh.startTime, wh.endTime)
                if wh.day == "Petak":
                    oh.addRange("Fr", wh.startTime, wh.endTime)
                if wh.day == "Subota":
                    oh.addRange("Sa", wh.startTime, wh.endTime)
                if wh.day == "Nedelja":
                    oh.addRange("Su", wh.startTime, wh.endTime)

            item["opening_hours"] = oh
            yield item
