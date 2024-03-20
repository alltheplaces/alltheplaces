import scrapy
from scrapy import Selector

from locations.hours import OpeningHours
from locations.items import Feature


class JJillSpider(scrapy.Spider):
    name = "jjill"
    item_attributes = {"brand": "J.Jill", "brand_wikidata": "Q64448268"}
    allowed_domains = ["jjill.com"]
    start_urls = ["https://locations.jjill.com/"]

    def parse(self, response):
        urls = response.xpath('//*[@class="indexpage_node"]/a/@href').extract()
        if urls:
            for url in urls:
                yield scrapy.Request(response.urljoin(url), callback=self.parse)
        else:
            name = response.xpath('//*[@class="store-name"]/text()').extract_first()
            street = response.xpath('//*[@itemprop="streetAddress"]//text()').extract_first()
            city = response.xpath('//*[@itemprop="addressLocality"]/text()').extract_first()
            state = response.xpath('//*[@itemprop="addressRegion"]/text()').extract_first()
            postalcode = response.xpath('//*[@itemprop="postalCode"]/text()').extract_first()
            country = response.xpath('//*[@itemprop="addressCountry"]/text()').extract_first()
            phone = response.xpath('//*[@itemprop="telephone"]/text()').extract_first()
            latitude = response.xpath('//*[@property="place:location:latitude"]/@content').extract_first()
            longitude = response.xpath('//*[@property="place:location:longitude"]/@content').extract_first()
            ref = response.url.strip("/").split("/")[-1]
            hours = response.xpath(
                '//h2[text()="Store Hours"]/following-sibling::div[@class="desktop"]/div[contains(@class, "day-hours")]'
            )
            properties = {
                "name": name.strip(),
                "ref": ref,
                "street": street.strip(),
                "city": city.strip(),
                "postcode": postalcode.strip(),
                "state": state.strip(),
                "country": country.strip(),
                "phone": phone.strip(),
                "website": response.url,
                "lat": float(latitude),
                "lon": float(longitude),
                "opening_hours": self.parse_hours(hours) if hours else None,
            }
            yield Feature(**properties)

    def parse_hours(self, store_hours: Selector) -> OpeningHours:
        opening_hours = OpeningHours()

        for rule in store_hours:
            day = rule.xpath('.//*[@class="day"]/text()').get().strip(" :")
            hours = rule.xpath('.//*[@class="hr"]/text()').get()
            if "closed" in hours.lower():
                continue
            start_time, end_time = hours.split("-")
            start_time = self.sanitise_time(start_time).replace(" ", "")
            end_time = self.sanitise_time(end_time).replace(" ", "")
            opening_hours.add_range(day, start_time, end_time, time_format="%I:%M%p")
        return opening_hours

    @staticmethod
    def sanitise_time(time: str) -> str:
        if ":" not in time:
            time = time.replace("am", ":00am").replace("pm", ":00pm")
        return time
