from locations.spiders.mazda_gr import MazdaGRSpider


class MazdaMTSpider(MazdaGRSpider):
    name = "mazda_mt"
    api_url = "https://www.mazda.com.mt/api/2sxc/app/auto/query/DealerListByPortalAlias/Default"
    module_id = "10025"
    tab_id = "2559"
    country = "MT"
