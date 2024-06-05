import scrapy

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MrBircolageBeSpider(scrapy.Spider):
    name = "mr_bricolage_be"
    item_attributes = {"brand": "Mr. Bricolage", "brand_wikidata": "Q3141657"}
    start_urls = ["https://www.mr-bricolage.be/magasins?ajax=1&all=1"]

    def parse(self, response):
        stores = response.xpath("/markers/marker")
        for store in stores:
            # There is a StoreNo but there is no more info.
            # ref = store.xpath("./StoreNo/text()").get()
            ref = store.xpath("./@id_store").get()
            name = store.xpath("./@name").get()
            phone = store.xpath("./@phone").get()
            city = store.xpath("./VisitCity/text()").get()
            lon = float(store.xpath("./@lng").get())
            lat = float(store.xpath("./@lat").get())
            website = "https://www.mr-bricolage.be" + store.xpath("./@link").get()

            properties = {
                "ref": ref,
                "name": name,
                "phone": phone,
                "city": city,
                "lon": lon,
                "lat": lat,
                "website": website,
            }

            if website:
                yield scrapy.http.Request(
                    url=website,
                    method="GET",
                    callback=self.add_website_info,
                    cb_kwargs={"properties": properties},
                )
            else:
                yield Feature(**properties)

    def add_website_info(self, response, properties):
        properties = self.get_address_info(response, properties)

        if opening_hours := self.parse_hours(response):
            properties["opening_hours"] = opening_hours

        yield Feature(**properties)

    def get_address_info(self, response, properties):
        addr_part = (
            response.xpath('//*[@class="advanced-cms-wrapper "]')
            .xpath('//*[@class="col-md-4"]//*[@class="rte"]/p[2]/text()')
            .getall()
        )

        if len(addr_part) == 2:
            street_address, postcode_city = self.clean_text(addr_part[0]), self.clean_text(addr_part[1])
        elif len(addr_part) == 1:
            street_address = self.clean_text(addr_part[0])
            postcode_city = self.clean_text(
                (
                    response.xpath('//*[@class="advanced-cms-wrapper "]')
                    .xpath('//*[@class="col-md-4"]//*[@class="rte"]/p[2]/text()')
                    .getall()
                )[0]
            )

        addr_full = clean_address([street_address, postcode_city])
        properties["addr_full"] = addr_full
        properties["street_address"] = street_address
        return properties

    def parse_hours(self, store):
        open_hours_path = store.xpath('//*[@class="advanced-cms-wrapper "]').xpath("//table/tbody")
        opening_hours = OpeningHours()

        for i in range(1, 8):
            if (day_path := open_hours_path.xpath(f"//tr[{i}]/td/text()").getall()) is not None:
                # Add Week days
                if len(day_path) == 2:
                    day, hours = self.clean_text(day_path[0]), self.clean_text(day_path[1])
                else:
                    day = self.clean_text(day_path[0])
                    hours = open_hours_path.xpath(f"//tr[{i}]/td[2]/span/text()").get()
                if hours != "Fermé":
                    open_hours, close_hours = hours.split(" ")[0], hours.split(" ")[2]
                    opening_hours.add_range(
                        day=DAYS_FR[day],
                        open_time=open_hours,
                        close_time=close_hours,
                        time_format="%H:%M",
                    )

        return opening_hours.as_opening_hours()

    def clean_text(self, text):
        return text.replace(",", "").replace("\xa0", " ")
