from locations.spiders.jb_hifi_au import JbHifiAUSpider


class JbHifiNZSpider(JbHifiAUSpider):
    name = "jb_hifi_nz"
    api_key = "74be29bb477b82649e40a534e494d26d"
    app_id = "VHBKEAHERO"
    domain = "co.nz"
