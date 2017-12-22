# -*- coding: utf-8 -*-
"""
Wafflehouse ...
"""
import scrapy
import re
from locations.items import GeojsonPointItem

class WaffleHouseSpider(scrapy.Spider):
    name = "wafflehouse"
    allowed_domains = ["wafflehouse.com"]
    start_urls = ('https://locations.wafflehouse.com/',)

    def parse(self, response):
        self.log(response.text)
        # # add to list of processed
        # self.crawled_sites.add(link_id)
        # address_1 = address['address1']
        # address_2 = address['address2']
        # full_address = address_1 + " " + address_2
        # city = address['city']
        # state = address['state']
        # country = address['country']
        # zip_code = address['zipcode']
        # latitude = address['latitude']
        # longitude = address['longitude']
        # phone = address['phone']
        # fax = address['fax']
        # open_hours = address['open_close_info']
        # website = address['order_url']
        #
        # properties = {"addr_full": full_address,
        #               "city": city,
        #               "state": state,
        #               "postcode": zip_code,
        #               "country": country,
        #               "phone": self.process_phone(phone),
        #               "website": website,
        #               "ref": link_id,
        #               "opening_hours": self.process_hours(open_hours),
        #               "extras": {"fax": self.process_phone(fax)},
        #               "lon": float(longitude),
        #               "lat": float(latitude)}
        # yield GeojsonPointItem(**properties)

    def process_phone(self, phone_number):
        """
        ...
        """
        pass

    def process_hours(self, hours):
        """
        ...
        """
        pass

    def am_pm(self, hr, a_p):
        """
            A convenience method to fix noon and midnight issues
        :param hr: the hour has to be passed in to accurately decide 12noon and midnight
        :param a_p: this is either a or p i.e am pm
        :return: the hours that must be added
        """
        diff = 0
        if a_p == 'AM':
            if int(hr) < 12:
                diff = 0
            else:
                diff = -12
        else:
            if int(hr) < 12:
                diff = 12
        return diff
