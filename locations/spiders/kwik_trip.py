import scrapy
from locations.items import GeojsonPointItem


class KwikTripSpider(scrapy.Spider):
    name = "kwiktrip"
    allowed_domains = ["www.kwiktrip.com"]
    download_delay = 0
    user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) " \
                 "AppleWebKit/537.36 (KHTML, like Gecko) " \
                 "Chrome/63.0.3239.84 Safari/537.36"
    start_urls = (
        'https://www.kwiktrip.com/Locations/Maps-Downloads/Store-List',
    )

    def parse_page(self, response):
        row = response.xpath('//tr')
        for i in row:
            storeid = i.xpath('./td[1]/text()').extract_first()
            name = i.xpath('./td[2]/text()').extract_first()
            street = i.xpath('./td[3]/text()').extract_first()
            city = i.xpath('./td[4]/text()').extract_first()
            state = i.xpath('./td[5]/text()').extract_first()
            postcode = i.xpath('./td[6]/text()').extract_first()
            phone = i.xpath('./td[7]/text()').extract_first()
            lat = i.xpath('./td[8]/text()').extract_first()
            lon = i.xpath('./td[9]/text()').extract_first()
            addr_full = "{} {}, {} {}".format(street, city, state, postcode)

            yield GeojsonPointItem(
                ref=storeid,
                name=name,
                street=street,
                city=city,
                state=state,
                postcode=postcode,
                addr_full=addr_full,
                phone=phone,
                lat=lat,
                lon=lon,
            )

    def parse(self, response):
        for i in range(8):
            yield scrapy.FormRequest.from_response(response, formdata={
                '__EVENTTARGET': 'p$lt$ctl04$pageplaceholder$p$lt$ctl03'
                                 '$KwikTrip_LocationsList$gridStores$p$p',
                '__EVENTARGUMENT': str(i),
                'p$lt$ctl04$pageplaceholder$p$lt$ctl03$KwikTrip_LocationsList'
                '$gridStores$p$drpPageSize': '100',
            }, dont_click=True, callback=self.parse_page)
