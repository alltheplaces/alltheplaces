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
                    oh.add("Mo", wh.startTime, wh.endTime)
                if wh.day == "Utorak":
                    oh.add("Tu", wh.startTime, wh.endTime)
                if wh.day == "Sreda":
                    oh.add("We", wh.startTime, wh.endTime)
                if wh.day == "Četvrtak":
                    oh.add("Th", wh.startTime, wh.endTime)
                if wh.day == "Petak":
                    oh.add("Fr", wh.startTime, wh.endTime)
                if wh.day == "Subota":
                    oh.add("Sa", wh.startTime, wh.endTime)
                if wh.day == "Nedelja":
                    oh.add("Su", wh.startTime, wh.endTime)

            item["opening_hours"] = oh
            yield item
