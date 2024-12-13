from locations.spiders.savers_ca_us import SaversCAUSSpider


class SaversAUSpider(SaversCAUSSpider):
    name = "savers_au"
    end_point = "https://maps.savers.com.au"
