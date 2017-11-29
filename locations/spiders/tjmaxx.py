# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class TjmaxxSpider(scrapy.Spider):
    name = "tjmaxx"
    allowed_domains = ["tjx.com", "tjmaxx.com"]
    start_urls = (
        'https://tjmaxx.tjx.com/store/stores/allStores.jsp',
    )

    def parse(self, response):
        links = response.xpath('//li[@class="storelist-item vcard address"]/a[@href]/@href')
        for link in links:
            yield scrapy.Request(
                response.urljoin(link.extract()),
                callback=self.parse_links
            )


    def parse_links(self, response):
        store_details = response.xpath('//form[@id="directions-form"]')
        for store in store_details:
            county = store.xpath('input[@name="storeName"]/@value').extract()
            hours = store.xpath('input[@name="hours"]/@value').extract()
            address = store.xpath('input[@name="address"]/@value').extract()
            city = store.xpath('input[@name="city"]/@value').extract()
            state = store.xpath('input[@name="state"]/@value').extract()
            zip = store.xpath('input[@name="zip"]/@value').extract()
            phone = store.xpath('input[@name="phone"]/@value').extract()
            latitude = store.xpath('input[@name="lat"]/@value').extract()
            longitude = store.xpath('input[@name="long"]/@value').extract()
            website = response.xpath('//head/link[@rel="canonical"]/@href')[0].extract()
            link_id = website.split("/")[-2]

        properties = {
                "addr:full": address[0],
                "addr:city": city[0],
                "addr:state": state[0],
                "addr:postcode": zip[0],
                "addr:country": "US",
                'phone': phone[0],
                'website': website,
                'ref': link_id,
                'opening_hours': self.process_hours(hours[0])
            }

        lon_lat = [
            float(longitude[0]),
            float(latitude[0]),
        ]

        yield GeojsonPointItem(
            properties = properties,
            lon_lat = lon_lat,
        )


    def process_hours(self, hours):
        """ This should capture these time formats as on tjmaxx
                # Mon-Wed: 9:30a-9:30p,
                # Thanksgiving Day: CLOSED,  <- this gets appended without modification
                # Fri-Sat: 7a-10p,
                # Sun: 9a-10p
        :param hours:
        :return:  string - in this format Mo-Th 11:00-12:00; Fr-Sa 11:00-01:00;
        """
        working_hour = []

        for t in hours.split(","):
            match = re.search(r"^((\w{2})\w(?:-(\w{2})\w)?\:\s(\d+)(\:\d+)?(\w)-(\d+)(\:\d+)?(\w))$",
                              t.strip(),
                              re.IGNORECASE)
            if match:
                m = list(match.groups())
                if len(m) == 9:
                    # replace second entry for day of week for formats like Sun: 9a-12p
                    if m[2] is None:
                        m[2] = ""
                    else:
                        m[2] = "-" + m[2]

                    # concatenate to our format
                    if m[4] is None:
                        if m[7] is None:
                            # time is like Mon-Wed: 9a-9p
                            working_hour.append(m[1] + m[2] + " " + str(int(m[3]) + self.am_pm(m[3], m[5])) + ":00-" +
                                                str(int(m[6]) + self.am_pm(m[6], m[8])) + ":00")
                        else:
                            # time is like Mon-Wed: 9a-9:30p
                            working_hour.append(m[1] + m[2] + " " + str(int(m[3]) + self.am_pm(m[3], m[5])) + ":00-" +
                                                str(int(m[6]) + self.am_pm(m[6], m[8])) + m[7])
                    else:
                        if m[7] is None:
                            # time is like Mon-Wed: 9:30a-9p
                            working_hour.append(m[1] + m[2] + " " + str(int(m[3]) + self.am_pm(m[3], m[5])) + m[4] +
                                                "-" + str(int(m[6]) + self.am_pm(m[6], m[8])) + ":00")
                        else:
                            # time is like Mon-Wed: 9:30a-9:30p
                            working_hour.append(m[1] + m[2] + " " + str(int(m[3]) + self.am_pm(m[3], m[5])) + m[4] +
                                                "-" + str(int(m[6]) + self.am_pm(m[6], m[8])) + m[7])
            # else:
            #     working_hour.append(t)

        if len(working_hour):
            return "; ".join(working_hour)
        else:
            # if something fails, return original date
            return hours

    def am_pm(self, m3, x):
        """
            A convenience method to fix noon and midnight issues
        :param m3: the hour has to be passed it to accurately decide 12noon and midnight
        :param x: this is either a or p i.e am pm
        :return: the hours that must be added

        """
        diff = 0
        if x == 'a':
            if int(m3) < 12:
                return_diff = 0
            else:
                return_diff = -12
        else:
            if int(m3) < 12:
                return_diff = 12
        return diff

