# This file is part of the Trezor project.
#
# Copyright (C) 2012-2018 SatoshiLabs and contributors
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the License along with this library.
# If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>.

import binascii
from decimal import Decimal
import requests
import json

from . import messages as proto
cache_dir = None


class TxApi(object):

    def __init__(self, network, url):
        self.network = network
        self.url = url
        self.pushtx_url = url

    def get_url(self, resource, resourceid):
        url = '%s%s/%s' % (self.url, resource, resourceid)
        return url

    def get_block(self, block_number):  # currunt block - block_number
        r = requests.get(self.url + 'blocks/')
        j = r.json(parse_float=str)
        block_height = j['blocks'][0]['height']
        block_height -= block_number
        r = requests.get(self.url + 'block-index/' + str(block_height))
        j = r.json(parse_float=str)
        block_hash = j['blockHash']
        block_hash_flipped = binascii.unhexlify("".join(reversed([block_hash[i:i + 2] for i in range(0, len(block_hash), 2)])))
        from struct import pack
        block_height_flipped = pack('<L', block_height)
        return block_hash_flipped, block_height_flipped

    def fetch_json(self, resource, resourceid):
        global cache_dir
        if cache_dir:
            cache_file = '%s/%s_%s_%s.json' % (cache_dir, self.network, resource, resourceid)
            try:  # looking into cache first
                j = json.load(open(cache_file), parse_float=str)
                return j
            except:
                pass

        try:
            url = self.get_url(resource, resourceid)
            r = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})
            j = r.json(parse_float=str)
        except:
            raise RuntimeError('URL error: %s' % url)
        if cache_dir and cache_file:
            try:  # saving into cache
                json.dump(j, open(cache_file, 'w'))
            except:
                pass
        return j

    def get_tx(self, txhash):
        raise NotImplementedError


class TxApiInsight(TxApi):

    def __init__(self, network, url, zcash=None, bip115=False):
        super(TxApiInsight, self).__init__(network, url)
        self.zcash = zcash
        self.pushtx_url = url.replace('/api/', '/tx/send')
        self.bip115 = bip115

    def get_tx(self, txhash):

        data = self.fetch_json('tx', txhash)

        t = proto.TransactionType()
        t.version = data['version']
        t.lock_time = data['locktime']

        for vin in data['vin']:
            i = t._add_inputs()
            if 'coinbase' in vin.keys():
                i.prev_hash = b"\0" * 32
                i.prev_index = 0xffffffff  # signed int -1
                i.script_sig = binascii.unhexlify(vin['coinbase'])
                i.sequence = vin['sequence']

            else:
                i.prev_hash = binascii.unhexlify(vin['txid'])
                i.prev_index = vin['vout']
                i.script_sig = binascii.unhexlify(vin['scriptSig']['hex'])
                i.sequence = vin['sequence']

        for vout in data['vout']:
            o = t._add_bin_outputs()
            o.amount = int(Decimal(vout['value']) * 100000000)
            o.script_pubkey = binascii.unhexlify(vout['scriptPubKey']['hex'])
            if(self.bip115 and len(o.script_pubkey) == 63 and o.script_pubkey[-1:] == b'\xb4'):
                o.block_hash = o.script_pubkey[-37:-5]
                o.block_height = o.script_pubkey[-4:-1]

            else:
                o.block_hash = None
                o.block_height = None

        if self.zcash:
            t.overwintered = data.get('fOverwintered', False)
            t.expiry = data.get('nExpiryHeight', False)
            if t.version >= 2:
                joinsplit_cnt = len(data['vjoinsplit'])
                if joinsplit_cnt == 0:
                    t.extra_data = b'\x00'
                else:
                    if joinsplit_cnt >= 253:
                        # we assume cnt < 253, so we can treat varIntLen(cnt) as 1
                        raise ValueError('Too many joinsplits')
                    extra_data_len = 1 + joinsplit_cnt * 1802 + 32 + 64
                    raw = self.fetch_json('rawtx', txhash)
                    raw = binascii.unhexlify(raw['rawtx'])
                    t.extra_data = raw[-extra_data_len:]

        return t


class TxApiBlockCypher(TxApi):

    def __init__(self, network, url, zcash=None):
        super(TxApiBlockCypher, self).__init__(network, url)
        self.pushtx_url = url.replace('//api.', '//live.').replace('/v1/', '/').replace('/main/', '/pushtx/')

    def get_tx(self, txhash):

        data = self.fetch_json('txs', txhash)

        t = proto.TransactionType()
        t.version = data['ver']
        t.lock_time = data.get('lock_time', 0)

        for vin in data['inputs']:
            i = t._add_inputs()
            if 'prev_hash' not in vin:
                i.prev_hash = b"\0" * 32
                i.prev_index = 0xffffffff  # signed int -1
                i.script_sig = binascii.unhexlify(vin['script'])
                i.sequence = vin['sequence']
            else:
                i.prev_hash = binascii.unhexlify(vin['prev_hash'])
                i.prev_index = vin['output_index']
                i.script_sig = binascii.unhexlify(vin['script'])
                i.sequence = vin['sequence']

        for vout in data['outputs']:
            o = t._add_bin_outputs()
            o.amount = int(str(vout['value']), 10)
            o.script_pubkey = binascii.unhexlify(vout['script'])

        return t
