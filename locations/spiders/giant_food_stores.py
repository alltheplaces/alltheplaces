import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class GiantFoodStoresSpider(SitemapSpider):
    name = "giant_food_stores"
    sitemap_urls = ["https://stores.giantfoodstores.com/robots.txt"]
    item_attributes = {"brand": "Giant", "brand_wikidata": "Q5558332"}

    sitemap_rules = [(r"^https://stores.giantfoodstores.com/[^/]*/[^/]*/[^/]*$", "parse")]

    def parse(self, response):
        main = response.xpath("//main")

        hours = OpeningHours()
        for day in json.loads(main.xpath('.//*[@id="store-hours"]//*[@data-days]/@data-days').get("[]")):
            if not day["intervals"]:
                hours.set_closed(day["day"])
            for interval in day["intervals"]:
                hours.add_range(day["day"], f"{interval['start']:04d}", f"{interval['end']:04d}", "%H%M")

        properties = {
            "ref": response.xpath('//div[@class="StoreDetails-storeNum"]/text()').get(),
            "website": response.url,
            "branch": main.css("[itemprop=name]").attrib["content"].removeprefix("GIANT "),
            "lat": main.css("[itemprop=latitude]").attrib["content"],
            "lon": main.css("[itemprop=longitude]").attrib["content"],
            "phone": main.css("[itemprop=telephone]::text").get(),
            "street_address": main.css("[itemprop=streetAddress]").attrib["content"],
            "city": main.css("[itemprop=addressLocality]").attrib["content"],
            "state": main.css("[itemprop=addressRegion]::text").get(),
            "postcode": main.css("[itemprop=postalCode]::text").get(),
            "opening_hours": hours,
        }

        apply_category(Categories.SHOP_SUPERMARKET, properties)

        return Feature(**properties)
