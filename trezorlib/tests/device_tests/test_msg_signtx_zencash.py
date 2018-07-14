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

from binascii import hexlify, unhexlify
import pytest

from .common import TrezorTest
from .conftest import TREZOR_VERSION

from trezorlib import coins
from trezorlib import messages as proto
from trezorlib.client import CallException
from trezorlib.tools import parse_path

TxApiTestnet = coins.tx_api['Zencash']


TXHASH_5c580d = unhexlify('5c580d7410c626cc3d0b40c8b61fe1902e2fd3b289aae17b16cbc6db16c86b4c')
TXHASH_adea9e = unhexlify('adea9eace4586b2fba2a6b1dac03fa1099a6c4f2a7ae841e20d973f064c14d85')


class TestMsgSigntx(TrezorTest):
    def test_two_one(self):
        self.setup_mnemonic_nopin_nopassphrase()

        # tx: 5c580d7410c626cc3d0b40c8b61fe1902e2fd3b289aae17b16cbc6db16c86b4c
        # input 1: 25000
        # tx: adea9eace4586b2fba2a6b1dac03fa1099a6c4f2a7ae841e20d973f064c14d85
        # input 1: 20000

        inp1 = proto.TxInputType(
            address_n=parse_path("44'/121'/0'/0/0"),  # 1CK7SJdcb8z9HuvVft3D91HLpLC6KSsGb
            prev_hash=TXHASH_5c580d,
            prev_index=0,
            prev_block_hash_bip115=unhexlify('efdca211d7c63deb490e1d4a0c573cef6cc949cc4322075f73c3190100000000'),
            prev_block_height_bip115=290311,
        )

        inp2 = proto.TxInputType(
            address_n=parse_path("44'/121'/0'/0/0"),  # 15AeAhtNJNKyowK8qPHwgpXkhsokzLtUpG
            prev_hash=TXHASH_adea9e,
            prev_index=0,
            prev_block_hash_bip115=unhexlify('fa59243883f41620bb833f73a01b18fee1915e68e805fe640403a02400000000'),
            prev_block_height_bip115=290314,
        )

        out1 = proto.TxOutputType(
            address='znmc8tf4ngHj6YmBr9QNPQMSwu9YwLV6XM6',
            amount=40000,
            script_type=proto.OutputScriptType.PAYTOADDRESS,
            block_hash_bip115=unhexlify('dfdd8aad03f9104a068aae49102926c4d92b1dc38a02b4a471556d2900000000'),
            block_height_bip115=291331,
        )

        with self.client:
            self.client.set_expected_responses([
                proto.TxRequest(request_type=proto.RequestType.TXINPUT, details=proto.TxRequestDetailsType(request_index=0)),
                proto.TxRequest(request_type=proto.RequestType.TXMETA, details=proto.TxRequestDetailsType(tx_hash=TXHASH_5c580d)),
                proto.TxRequest(request_type=proto.RequestType.TXINPUT, details=proto.TxRequestDetailsType(request_index=0, tx_hash=TXHASH_5c580d)),
                proto.TxRequest(request_type=proto.RequestType.TXOUTPUT, details=proto.TxRequestDetailsType(request_index=0, tx_hash=TXHASH_5c580d)),
                proto.TxRequest(request_type=proto.RequestType.TXINPUT, details=proto.TxRequestDetailsType(request_index=1)),
                proto.TxRequest(request_type=proto.RequestType.TXMETA, details=proto.TxRequestDetailsType(tx_hash=TXHASH_adea9e)),
                proto.TxRequest(request_type=proto.RequestType.TXINPUT, details=proto.TxRequestDetailsType(request_index=0, tx_hash=TXHASH_adea9e)),
                proto.TxRequest(request_type=proto.RequestType.TXOUTPUT, details=proto.TxRequestDetailsType(request_index=0, tx_hash=TXHASH_adea9e)),
                proto.TxRequest(request_type=proto.RequestType.TXOUTPUT, details=proto.TxRequestDetailsType(request_index=0)),
                proto.ButtonRequest(code=proto.ButtonRequestType.ConfirmOutput),
                proto.ButtonRequest(code=proto.ButtonRequestType.SignTx),
                proto.TxRequest(request_type=proto.RequestType.TXINPUT, details=proto.TxRequestDetailsType(request_index=0)),
                proto.TxRequest(request_type=proto.RequestType.TXINPUT, details=proto.TxRequestDetailsType(request_index=1)),
                proto.TxRequest(request_type=proto.RequestType.TXOUTPUT, details=proto.TxRequestDetailsType(request_index=0)),
                proto.TxRequest(request_type=proto.RequestType.TXINPUT, details=proto.TxRequestDetailsType(request_index=0)),
                proto.TxRequest(request_type=proto.RequestType.TXINPUT, details=proto.TxRequestDetailsType(request_index=1)),
                proto.TxRequest(request_type=proto.RequestType.TXOUTPUT, details=proto.TxRequestDetailsType(request_index=0)),
                proto.TxRequest(request_type=proto.RequestType.TXOUTPUT, details=proto.TxRequestDetailsType(request_index=0)),
                proto.TxRequest(request_type=proto.RequestType.TXFINISHED),
            ])
            (signatures, serialized_tx) = self.client.sign_tx('Zencash', [inp1, inp2], [out1, ])

        # Accepted by network:
        assert hexlify(serialized_tx) == b'01000000024c6bc816dbc6cb167be1aa89b2d32f2e90e11fb6c8400b3dcc26c610740d585c000000006a473044022040bee40d16bf1e58add23c2db89d98d630c3d718cc9eb1a6b9a04b399d60643a02201f908f0de659e768d558ea7a86c9b82f7638b90f66c88f16886a959175af8e27012102c33d152614eb61743ca024ff731324538b0bd7eee667641952fc2d7f9840d704ffffffff854dc164f073d9201e84aea7f2c4a69910fa03ac1d6b2aba2f6b58e4ac9eeaad000000006a47304402204ff56d26e7f1b136b9c721a9f61c113686d2acb081a239dfa7c8af502a2e290c02205ed14bc906ffe62e12d477e594ad6f6e86a7bc4da9745dc3ea8441ecebaf4622012102c33d152614eb61743ca024ff731324538b0bd7eee667641952fc2d7f9840d704ffffffff01409c0000000000003f76a914e119c36bb1d348bad3e0eb9c4f5a6421a006f6ee88ac20dfdd8aad03f9104a068aae49102926c4d92b1dc38a02b4a471556d290000000003037204b400000000'
