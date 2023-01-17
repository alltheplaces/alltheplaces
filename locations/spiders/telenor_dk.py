from scrapy import Selector, Spider

from locations.items import Feature


class TelenorDKSpider(Spider):
    name = "telenor_dk"
    item_attributes = {
        "brand": "Telenor",
        "brand_wikidata": "Q1796954",
        "country": "DK",
    }
    start_urls = ["https://www.telenor.dk/da/custom/FindNearestShopBlock/GetShops/2bd5f376-3f79-475b-aa1e-b45174b9a2f3/?blockId=1590"]

    def parse(self, response):
        for store in response.json():
            item = Feature()

            item["lon"] = store["longitude"]
            item["lat"] = store["latitude"]

            item["phone"] = store["html"].xpath("//p").get()[8].strip().split(": ")[1]

            item["street_address"] = store["html"].xpath("//p").get()[2].strip()
            item["poscode"] = store["html"].xpath("//p").get()[3].strip().split(" ")[0]
            item["city"] = store["html"].xpath("//p").get()[3].strip().split(" ")[1]

            oh = OpeningHours()
            opening_hours = store["html"].xpath('//div["@classborder--bottom padding-trailer"][2]//p/text()').get()
            for(rule in openning_hours)
              rule = rule.strip().split(": ")
              day = rule[0];
              if(day=="Hverdage")
                oh.add("Mo-Fr "+rule[1])
              elif(day=="Lørdag")
                oh.add("Sa "+rule[1])
              elif(day=="Søndag")
                oh.add("Su "+rule[1])

            yield item
