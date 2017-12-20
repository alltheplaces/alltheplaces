import scrapy
from locations.items import GeojsonPointItem

base_url = 'https://216.222.184.133/main/storeDetails.html?store='
store_list = [str(i) for i in range(3012, 3345)]
bad_urls = ['3014', '3019', '3023', '3024', '3026', '3027', '3031', '3033',
            '3035', '3037', '3038', '3039', '3044', '3048', '3049', '3051',
            '3061', '3062', '3063', '3066', '3067', '3069', '3075', '3076',
            '3077', '3078', '3079', '3099', '3100', '3110', '3116', '3117',
            '3118', '3122', '3124', '3238', '3239', '3327', '3336', '3339',
            '3344']

for i in bad_urls:
    store_list.remove(i)


class MenardsSpider(scrapy.Spider):
    name = 'menards'
    download_delay = 0
    allowed_domains = ['216.222.184.133']
    start_urls = ['http://216.222.184.133/main/storeDetails.html?store=3011']

    def parse(self, response):
        if response.status == 200:
            store_id = response.url.split('=')[1]
            store_name = response.xpath(
                '//*[@id="mainContent"]/div[1]/div[1]/h1/text()')\
                .extract_first()
            street = response.xpath(
                '//*[@id="mainContent"]/div[1]/div[1]/text()[2]')\
                .extract_first().strip()
            cty_st_zip = response.xpath(
                '//*[@id="mainContent"]/div[1]/div[1]/text()[3]')\
                .extract_first()
            city = cty_st_zip.split(',')[0].strip()
            state = cty_st_zip.split(', ')[1].split(' ')[0]
            postcode = cty_st_zip.split(', ')[1].split(' ')[1]

            addr_full = "{} {}, {} {}".format(
                street, city, state, postcode)

            yield GeojsonPointItem(
                ref=store_id,
                name=store_name,
                street=street,
                city=city,
                state=state,
                postcode=postcode,
                addr_full=addr_full
            )

            nearby_stores = response.xpath(
                '//*[@id="mainContent"]/div[1]/div[5]/ol/li')
            for i in nearby_stores:
                nrby_id = i.xpath(
                    './/p[5]/a/@href').extract_first().split('=')[1]
                nrby_name = i.xpath(
                    './/p[1]/strong/text()').extract_first()
                nrby_street = i.xpath(
                    './/p[2]/text()').extract_first().strip()
                nrby_cty_st_zip = i.xpath(
                    './/p[3]/text()').extract_first()
                nrby_city = nrby_cty_st_zip.split(',')[0].strip()
                nrby_state = nrby_cty_st_zip.split(', ')[1].split(' ')[0]
                nrby_postcode = nrby_cty_st_zip.split(', ')[1].split(' ')[1]

                nrby_addr_full = "{} {}, {} {}".format(
                    nrby_street, nrby_city, nrby_state, nrby_postcode)

                # Remove nearby stores from list to crawl to reduce requests
                if nrby_id in store_list:
                    store_list.remove(nrby_id)

                yield GeojsonPointItem(
                    ref=nrby_id,
                    name=nrby_name,
                    street=nrby_street,
                    city=nrby_city,
                    state=nrby_state,
                    postcode=nrby_postcode,
                    addr_full=nrby_addr_full
                )

        if store_list:
            yield scrapy.Request(base_url + store_list[0], meta={
                'dont_redirect': True, 'handle_httpstatus_all': True})
            store_list.remove(store_list[0])
