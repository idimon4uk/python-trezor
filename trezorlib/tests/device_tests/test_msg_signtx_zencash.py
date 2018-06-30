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
            prev_block_height_bip115=unhexlify('076e04'),
        )

        inp2 = proto.TxInputType(
            address_n=parse_path("44'/121'/0'/0/0"),  # 15AeAhtNJNKyowK8qPHwgpXkhsokzLtUpG
            prev_hash=TXHASH_adea9e,
            prev_index=0,
            prev_block_hash_bip115=unhexlify('fa59243883f41620bb833f73a01b18fee1915e68e805fe640403a02400000000'),
            prev_block_height_bip115=unhexlify('0a6e04'),
        )

        out1 = proto.TxOutputType(
            address='znmc8tf4ngHj6YmBr9QNPQMSwu9YwLV6XM6',
            amount=40000,
            script_type=proto.OutputScriptType.PAYTOADDRESS,
            block_hash_bip115=unhexlify('dfdd8aad03f9104a068aae49102926c4d92b1dc38a02b4a471556d2900000000'),
            block_height_bip115=unhexlify('037204'),
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

        print(hexlify(serialized_tx))
        assert hexlify(serialized_tx) == b'01000000021c032e5715d1da8115a2fe4f57699e15742fe113b0d2d1ca3b594649d322bec6010000006b483045022100f773c403b2f85a5c1d6c9c4ad69c43de66930fff4b1bc818eb257af98305546a0220443bde4be439f276a6ce793664b463580e210ec6c9255d68354449ac0443c76501210338d78612e990f2eea0c426b5e48a8db70b9d7ed66282b3b26511e0b1c75515a6ffffffff6ea42cd8d9c8e5441c4c5f85bfe50311078730d2881494f11f4d2257777a4958010000006b48304502210090cff1c1911e771605358a8cddd5ae94c7b60cc96e50275908d9bf9d6367c79f02202bfa72e10260a146abd59d0526e1335bacfbb2b4401780e9e3a7441b0480c8da0121038caebd6f753bbbd2bb1f3346a43cd32140648583673a31d62f2dfb56ad0ab9e3ffffffff02a0860100000000001976a9142f4490d5263906e4887ca2996b9e207af3e7824088aca0860100000000001976a914812c13d97f9159e54e326b481b8f88a73df8507a88ac00000000'
