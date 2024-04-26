from typing import Iterable

from scrapy import Request
from scrapy.http import TextResponse

from store_scrap.spiders.storescrap import StoreScrapSpider
from store_scrap.items import Product


class CarrefourksaSpider(StoreScrapSpider):
    name = "carrefour_ksa"
    allowed_domains = ['carrefourksa.com']
    api = 'https://www.carrefourksa.com/api/v8/search?keyword={keyword}&filter=product_category_level_1_ar:%27NFKSA4000000%27&sortBy=relevance&currentPage={page}&pageSize={per_page}&maxPrice=&minPrice=&areaCode=Granada%20-%20Riyadh&lang=ar&nextOffset=0&disableSpellCheck=&displayCurr=SAR&latitude=24.7136&longitude=46.6753&asgCategoryId=&asgCategoryName=&needVariantsData=true&requireSponsProducts=true&responseWithCatTree=true&depth=3'

    per_page = 60

    brand_values = {
        'Konka': 'كونكا',
        'Admiral': 'أدميرال',
        'Hisense': 'هايسنس',
        'Samsung': 'سامسونج',
    }

    def __init__(self, brands=tuple(brand_values.keys()), **kwargs):
        super().__init__(brands=brands, **kwargs)
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            # "If-Modified-Since": "Fri, 26 Apr 2024 00:39:30 GMT",
            # "If-None-Match": "W/\"8799-OPhT1n4dmV2UtZNTg5s/gNvutKY\"",
            # "Referer": "https://www.carrefourksa.com/mafsau/ar/v4/search?keyword=%u0643%u0648%u0646%u0643%u0627",
            "Referer": self.origin,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
            "appid": "Reactweb",
            "credentials": "include",
            # "deviceid": "1541248235.1714091921",
            "env": "prod",
            "intent": "STANDARD",
            # "newrelic": "eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjMzNTU3MjAiLCJhcCI6IjEwMjE4NDU3MDUiLCJpZCI6IjVkOWE1MDY2NGU3ZDM1M2UiLCJ0ciI6IjU2NWY0NmJkMjg0NzgxMTA3MzQ0ZWVkYzYzMjA1NjVjIiwidGkiOjE3MTQwOTI3NzIzOTJ9fQ==",
            # "posinfo": "food=301_Zone01,nonfood=301_Zone01,express=303_Zone02",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "storeid": "mafsau",
            "token": "undefined",
            # "traceparent": "00-565f46bd284781107344eedc6320565c-5d9a50664e7d353e-01",
            # "tracestate": "3355720@nr=0-1-3355720-1021845705-5d9a50664e7d353e----1714092772392",
            # "userid": "858ACF1E-0D7E-0DDD-FC9E-0094DEE4A9CD"
        }

    def start_requests(self) -> Iterable[Request]:
        for brand in self.brands:
            if brand in self.brand_values:
                yield Request(
                    url=self.api.format(keyword=self.brand_values[brand], page=0, per_page=self.per_page),
                    headers=self.headers,
                    callback=self.parse,
                    cb_kwargs={'brand_ar': self.brand_values[brand], 'page': 0}
                )

    def parse(self, response: TextResponse, brand_ar: str, page: int) -> Iterable[Product]:
        response_json = response.json()
        for product_json in response_json['products']:
            yield Product(
                name_ar=product_json['name'],
                brand_ar=brand_ar,
                brand_en=product_json['brand']['name'],
                price_original=product_json['price']['price'],
                price_discounted=product_json['price'].get('discount', {}).get('price', ''),
                link=response.urljoin(product_json['links']['productUrl']['href']),
                sku=self.get_model_code(product_json['name'])
            )
        if response_json['totalProducts'] > (page + 1) * self.per_page:
            yield Request(
                url=self.api.format(keyword=brand_ar, page=page + 1, per_page=self.per_page),
                headers=self.headers,
                callback=self.parse,
                cb_kwargs={'brand_ar': brand_ar, 'page': page + 1}
            )

    @property
    def origin(self):
        return "https://www.carrefourksa.com/"
