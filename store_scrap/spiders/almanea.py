import json
from typing import Iterable
from urllib.parse import urljoin

from jsonpath_ng import parse
from scrapy.http import JsonRequest, TextResponse, Request
from w3lib.html import remove_tags

from store_scrap.items import Product
from store_scrap.spiders.storescrap import StoreScrapSpider


class AlmaneaSpider(StoreScrapSpider):
    name = "almanea"
    allowed_domains = ["almanea.sa"]

    region_id = "1101"

    cookies = {
        "__Secure-next-auth.callback-url": "https%3A%2F%2Fwww.almanea.sa%2F",
        "region_id": region_id
    }

    search_api = 'https://www.almanea.sa/api/filterSortedProducts/category'

    brand_values = {
        'Samsung': {"name": "سامسونج", "id": "117"},
        'Hisense': {"name": "هايسنس", "id": "144"},
    }

    handshake_url = 'https://www.almanea.sa/api/handshake?lang=ar'
    csrf_url = 'https://www.almanea.sa/api/auth/csrf'

    def get_payload(self, brand_name, brand_id, page=0):
        return {
            "url":f"facets/searchV2/{brand_name}?pageSize=20&pageNo={page}&sortBy=position&sortDir=DESC&select={self.region_id}&regionId={self.region_id}&brand={brand_id}"
        }

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            url=self.handshake_url,
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_handshake
        )

    def parse_handshake(self, response: TextResponse):
        self.cookies['handshake'] = response.json()['data']['token']
        yield Request(
            url=self.csrf_url,
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_csrf
        )

    def parse_csrf(self, response: TextResponse):
        self.cookies['__Host-next-auth.csrf-token'] = response.json()['csrfToken']
        for brand in self.brands:
            if brand in self.brand_values:
                brand_id = self.brand_values[brand]['id']
                brand_name = self.brand_values[brand]['name']
                yield JsonRequest(
                    url=self.search_api,
                    headers=self.headers,
                    cookies=self.cookies,
                    data=self.get_payload(brand_name, brand_id),
                    callback=self.parse,
                    cb_kwargs={'brand_name': brand_name, 'brand_id': brand_id},
                )

    @staticmethod
    def get_field_value(json_data, field_name):
        return parse(f'$..{field_name}').find(json_data).pop().value


    def parse(self, response: TextResponse, brand_name, brand_id):
        json_data = response.json()
        pages = self.get_field_value(json_data, 'pages')
        current_page = self.get_field_value(json_data, 'currentpage')
        for product_data in parse('$..products[*]._source').find(json_data):
            product_data = product_data.value
            name_ar = self.get_field_value(product_data, '$.name').pop()
            product = Product(
                name_ar=name_ar,
                price_original=self.get_field_value(product_data, 'original_price'),
                price_discounted=self.get_field_value(product_data, 'price'),
                brand_ar=self.get_field_value(product_data, 'option_text_brand').pop(),
                link=urljoin(
                    'https://www.almanea.sa/product/',
                    self.get_field_value(product_data, 'url_key').pop(),
                ),
                description_ar=remove_tags(product_data.get('short_description', [''])[0]).strip(),
                sku=self.get_model_code(name_ar),
                id=product_data['sku']
            )
            if not product['sku']:
                yield Request(
                    url=product['link'],
                    headers=self.headers,
                    cookies=self.cookies,
                    callback=self.parse_pdp,
                    cb_kwargs={'product': product}
                )
            else:
                yield product
        if current_page < pages:
            yield JsonRequest(
                url=self.search_api,
                headers=self.headers,
                cookies=self.cookies,
                data=self.get_payload(brand_name, brand_id, page=current_page + 1),
                callback=self.parse,
                cb_kwargs={'brand_name': brand_name, 'brand_id': brand_id},
            )

    def parse_pdp(self, response: TextResponse, product: Product):
        json_data = json.loads(response.css('script#__NEXT_DATA__::text').get())
        product['sku'] = self.get_field_value(json_data, 'pageProps.product.model').pop()
        yield product

    @property
    def origin(self):
        return 'https://www.almanea.sa/'
