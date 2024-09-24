import re

import scrapy

from locations.items import Feature


class FairwayMarketSpider(scrapy.Spider):
    name = "fairway_market"
    item_attributes = {"brand": "Fairway Market", "brand_wikidata": "Q5430911"}
    allowed_domains = ["http://www.fairwaymarkets.com/"]
    start_urls = (
        "http://www.fairwaymarkets.com/index.php/store-locations/victoria",
        "http://www.fairwaymarkets.com/index.php/store-locations/sidney",
        "http://www.fairwaymarkets.com/index.php/store-locations/brentwood",
        "http://www.fairwaymarkets.com/index.php/store-locations/nanaimo",
    )

    def parse(self, response):
        data = response.xpath('//div[@class="art-content-wide"]')
        for store in data.xpath('.//div[@class="art-Post-inner"]'):
            properties = {
                "ref": store.xpath('div[@class="art-PostContent"]/div[@class="art-article"]/p/text()').extract_first(),
                "addr_full": store.xpath(
                    'div[@class="art-PostContent"]/div[@class="art-article"]/p/text()'
                ).extract_first(),
                "name": store.xpath('h2/span[@class="art-PostHeader"]/text()').extract_first().replace("\n", ""),
                "city": self.city(
                    store.xpath('div[@class="art-PostContent"]/div[@class="art-article"]/p/text()')[1].extract()
                ),
                "state": self.state(
                    store.xpath('div[@class="art-PostContent"]/div[@class="art-article"]/p/text()')[1].extract()
                ),
                "postcode": store.xpath('div[@class="art-PostContent"]/div[@class="art-article"]/p/text()')[
                    2
                ].extract(),
                "opening_hours": self.store_hours(
                    store.xpath(
                        'div[@class="art-PostContent"]/div[@class="art-article"]/p/strong/text()'
                    ).extract_first()
                ),
                # "lon": float(store.xpath('longitude/text()').extract_first()),
                # "lat": float(store.xpath('latitude/text()').extract_first()),
            }

            yield Feature(**properties)
        else:
            self.logger.info("No results")

    def city(self, data):
        str_list = data.split(",")
        return str_list[0].strip()

    def state(self, data):
        str_list = data.split(",")
        state = str_list[1].strip()
        return state

    def store_hours(self, store_hours):
        if "day" not in store_hours and "-" not in store_hours:
            return ""
        days = "Mo-Su"
        hours = ""
        match = re.search(r"(\d{1,2})(A|P)M to (\d{1,2})(A|P)M", store_hours)
        if match:
            (f_hr, f_ampm, t_hr, t_ampm) = match.groups()
            f_hr = int(f_hr)
            if f_ampm == "P":
                f_hr += 12
            elif f_ampm == "A" and f_hr == 12:
                f_hr = 0
            t_hr = int(t_hr)
            if t_ampm == "P":
                t_hr += 12
            elif t_ampm == "A" and t_hr == 12:
                t_hr = 0

            hours = "{:02d}:{}-{:02d}:{}".format(
                f_hr,
                "00",
                t_hr,
                "00",
            )

        return days + " " + hours
