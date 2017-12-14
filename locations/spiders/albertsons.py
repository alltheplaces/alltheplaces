import json
import re
import scrapy
from locations.items import GeojsonPointItem


class AlbertsonsSpider(scrapy.Spider):
    name = "albertsons"
    allowed_domains = ["locator.safeway.com"]

    def parse_day(self, day):
        if re.search('Open 24 hours', day) :
            return ''
        if re.search('Open Daily', day) :
            return 'Mo-Su'
        regex = r"([A-Z][a-z]{2})(-([A-Z][a-z]{2})|)"
        matches = re.search(regex, day)
        if matches:
            day = matches.group()
        else:
            return ''
        if len(day)==3:
            return day[:2]
        if re.search('-', day):
            days = day.split('-')
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = day[:2]
                    osm_days.append(osm_day)
            return "-".join(osm_days)

    def parse_times(self, times):
            if times.strip() == 'Open 24 hours':
                return '24/7'
            regex = r"[0-9]{1,2}:[0-9]{1,2} [ap]m - (Midnight|([0-9]{1,2}:[0-9]{1,2} [ap]m))"
            matches = re.search(regex, times)
            if matches:
                times = matches.group()
            else:
                return ''
            hours_to = [x.strip() for x in times.split('-')]
            cleaned_times = []
            for hour in hours_to:
                if re.search('pm$', hour):
                    hour = re.sub('pm', '', hour).strip()
                    hour_min = hour.split(":")
                    if int(hour_min[0]) < 12:
                        hour_min[0] = str(12 + int(hour_min[0]))
                    cleaned_times.append(":".join(hour_min))

                if re.search('am$', hour):
                    hour = re.sub('am', '', hour).strip()
                    hour_min = hour.split(":")
                    if len(hour_min[0]) <2:
                        hour_min[0] = hour_min[0].zfill(2)
                    else:
                        hour_min[0] = str(int(hour_min[0]))

                    cleaned_times.append(":".join(hour_min))
                if re.search('Midnight', hour):
                    cleaned_times.append("Midnight")
            return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        if(lis==None):
            return ''
        else:
            lis = lis.split('<br/>')
            for li in lis:
                 parsed_time = self.parse_times(li)
                 parsed_day = self.parse_day(li)
                 hours.append(parsed_day + ' ' + parsed_time)
            return "; ".join(hours)
    def start_requests(self):
        zipcodes = ['83253', '57638', '54848', '44333', '03244', '23435', '31023', '38915', '79525', '81321', '89135', '98250',
                    '69154', '62838', '89445', '93204', '59402', '57532', '69030', '65231', '70394', '78550', '32566', '33185',
                    '27229', '16933', '41231', '46992']

        for zipcode in zipcodes:
            url = 'http://locator.safeway.com/ajax?&xml_request=%3Crequest%3E%3Cappkey%3EC8EBB30E-9CDD-11E0-9770-6DB40E5AF53B%3C%2Fappkey%3E%3Cformdata+id%3D%22locatorsearch%22%3E%3Cevents%3E%3Cwhere%3E%3Ceventstartdate%3E%3Cge%3Enow()%3C%2Fge%3E%3C%2Feventstartdate%3E%3C%2Fwhere%3E%3Climit%3E2%3C%2Flimit%3E%3C%2Fevents%3E%3Cdataview%3Estore_default%3C%2Fdataview%3E%3Cgeolocs%3E%3Cgeoloc%3E%3Caddressline%3E'+zipcode+'%3C%2Faddressline%3E%3Clongitude%3E%3C%2Flongitude%3E%3Clatitude%3E%3C%2Flatitude%3E%3Ccountry%3EUS%3C%2Fcountry%3E%3C%2Fgeoloc%3E%3C%2Fgeolocs%3E%3Csearchradius%3E1000%3C%2Fsearchradius%3E%3Cstateonly%3E1%3C%2Fstateonly%3E%3Climit%3E20000%3C%2Flimit%3E%3Cwhere%3E%3Ccountry%3EUS%3C%2Fcountry%3E%3Cclosed%3E%3Cdistinctfrom%3E1%3C%2Fdistinctfrom%3E%3C%2Fclosed%3E%3Cfuelparticipating%3E%3Cdistinctfrom%3E1%3C%2Fdistinctfrom%3E%3C%2Ffuelparticipating%3E%3Cbakery%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fbakery%3E%3Cdeli%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fdeli%3E%3Cfloral%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ffloral%3E%3Cliquor%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fliquor%3E%3Cmeat%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fmeat%3E%3Cpharmacy%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fpharmacy%3E%3Cproduce%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fproduce%3E%3Cjamba%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fjamba%3E%3Cseafood%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fseafood%3E%3Cstarbucks%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fstarbucks%3E%3Cvideo%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fvideo%3E%3Cfuelstation%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ffuelstation%3E%3Cdvdplay_kiosk%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fdvdplay_kiosk%3E%3Ccoinmaster%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fcoinmaster%3E%3Cwifi%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fwifi%3E%3Cbank%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fbank%3E%3Cseattlesbestcoffee%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fseattlesbestcoffee%3E%3Cbeveragestewards%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fbeveragestewards%3E%3Cphoto%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fphoto%3E%3Cwu%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fwu%3E%3Cdebi_lilly_design%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fdebi_lilly_design%3E%3Cdelivery%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fdelivery%3E%3Cfresh_cut_produce%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ffresh_cut_produce%3E%3Cquest_lab%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fquest_lab%3E%3C%2Fwhere%3E%3C%2Fformdata%3E%3C%2Frequest%3E'
            yield scrapy.Request(
                url=url,
                callback=self.parse
            )

    def parse(self, response):
        data = response.xpath('//poi')
        for store in data:
                properties = {
                    "ref": str(store.xpath('./uid/text()').extract_first()),
                    "name": store.xpath('./name/text()').extract_first(),
                    "opening_hours": self.parse_hours(store.xpath('./storehours1/text()').extract_first()),
                    "website": 'http://www1.albertsons.com/ShopStores/tools/store-locator.page',
                    "addr_full": store.xpath('./address1/text()').extract_first(),
                    "city": store.xpath('./city/text()').extract_first(),
                    "state": store.xpath('./state/text()').extract_first(),
                    "postcode": store.xpath('./postalcode/text()').extract_first(),
                    "country": store.xpath('./country/text()').extract_first(),
                    "lon": float(store.xpath('./longitude/text()').extract_first()),
                    "lat": float(store.xpath('./latitude/text()').extract_first()),
                }

                yield GeojsonPointItem(**properties)

