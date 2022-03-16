import os
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from dataclasses import dataclass
from urllib.parse import quote_plus
from typing import Optional, Dict, Any
import msgpack, base64, datetime, random, logging, time, urllib3, requests, json, hmac

class OAuthCrypto:

    def __init__(self, app_secret, rsa_key, app_id):
        self.app_secret = app_secret
        self.rsa_key = rsa_key
        self.app_id = app_id

    def generate_signature(self, data: bytes, hash_function, key):
        hashed_string = hash_function.new(data)
        signature = pkcs1_15.new(key).sign(hashed_string)
        return base64.b64encode(signature)

    def generate_nonce(self, length=19):
        return int(''.join([str(random.randint(0, 9)) for i in range(length)]))

    def build_oauth_header_entry(self, rest_method: str, full_url: str, body_data: bytes, uuid: Optional[str] = None,
                                 new_account: bool=False, extra_header: Dict[str, Any]=None):

        timestamp = int(time.time())
        oauth_header = {
            "oauth_body_hash": f"{base64.b64encode(SHA1.new(body_data).digest()).decode()}",
            "oauth_consumer_key": f"{self.app_id}",
            "oauth_nonce": f"{self.generate_nonce()}",
            "oauth_signature_method": f"{'HMAC-SHA1' if new_account else 'RSA-SHA1'}",
            "oauth_timestamp": f"{timestamp}",
            "oauth_version": "1.0"
        }

        oauth_header.update(extra_header or {})

        if not new_account:
            to_hash = (self.app_secret + str(timestamp)).encode()
            param_signature = self.generate_signature(to_hash, SHA1, self.rsa_key)
            oauth_header["xoauth_as_hash"] = param_signature.strip()
            oauth_header["xoauth_requestor_id"] = uuid

        auth_string = ""
        for key, value in sorted(oauth_header.items()):
            if key == "oauth_signature":
                continue
            auth_string += quote_plus(key)
            auth_string += "="
            auth_string += quote_plus(value)
            auth_string += "&"

        string_to_hash = quote_plus(rest_method) + "&" + \
                         quote_plus(full_url) + "&" + \
                         quote_plus(auth_string.rsplit("&", 1)[0])  # Todo: Comment

        if new_account:
            oauth_signature = hmac.new(self.app_secret.encode(), string_to_hash.encode(), "SHA1").digest()
            oauth_signature = base64.b64encode(oauth_signature)
        else:
            oauth_signature = self.generate_signature(string_to_hash.encode(), SHA1, self.rsa_key)

        oauth_header["oauth_signature"] = oauth_signature

        oauth_header_entry = "OAuth "
        for key, value in sorted(oauth_header.items()):
            oauth_header_entry += key
            oauth_header_entry += "=\""
            oauth_header_entry += quote_plus(value)
            oauth_header_entry += "\","
        oauth_header_entry = oauth_header_entry[:-1]
        return oauth_header_entry

class OAuthPayment:
    BN_PAYMENT_URL = "https://bn-payment-us.wrightflyer.net"

    def __init__(self, device_info, rsa_key, device_id, request_session, app_id, app_version, uuid):
        self.device_info = device_info
        self.rsa_key = rsa_key
        self.device_id = device_id
        self.request_session = request_session
        self.uuid = uuid
        self.x_uid = None
        self.app_version = app_version
        self.oauth_crypto = OAuthCrypto('e445e20c003fefbbb190502447f6a262', self.rsa_key, app_id)
        self.migration_code = None

    def _prepare_request(self, rest_type: str, resource: str, data, extra_header=None):
        new_account = self.uuid is None
        authorization = self.oauth_crypto.build_oauth_header_entry(rest_type, self.BN_PAYMENT_URL + resource,
                                                                   data, self.uuid, new_account,
                                                                   extra_header)

        header = self.device_info.get_bn_payment_header(authorization, self.app_version)
        self.request_session.headers = header

    def payment_authorize(self):
        authorize_endpoint = "/v1.0/auth/authorize"

        self._prepare_request("POST", authorize_endpoint, b"")
        self.request_session.post(self.BN_PAYMENT_URL + authorize_endpoint)

    def payment_device_verification(self):
        nonce = "/v1.0/deviceverification/nonce"

        self._prepare_request("POST", nonce, b"")
        self.request_session.post(self.BN_PAYMENT_URL + nonce)

        verify_endpoint = "/v1.0/deviceverification/verify"
        verification_payload = {
            "device_id": f"{self.device_id}",
            "compromised": False,
            "emulator": False,
            "debug": False,
            "installer": "com.android.vending",
            "bundle_id": "com.nexon.sinoalice",
            "app_version": self.app_version,
            "os_version": "10",
            "sf_jws": ""
        }

        payload = json.dumps(verification_payload).encode()

        self._prepare_request("POST", verify_endpoint, payload)
        self.request_session.post(self.BN_PAYMENT_URL + verify_endpoint, payload)

@dataclass(unsafe_hash=True)
class DeviceInfo():
    deviceModel: str = "Samsung Galaxy Note10"
    numericCountryCode: int = 840

    carrier: str = "Vodafone"
    country_code: str = "US"
    auth_version: str = "1.4.10"
    store_type: str = "google"
    uaType: str = "android-app"
    currency_code: str = "USD"

    us_or_jp = "us"
    host_payment: str = f"bn-payment-{us_or_jp}.wrightflyer.net"
    host_moderation: str = f"bn-moderation-{us_or_jp}.wrightflyer.net"

    def get_bn_payment_header(self, authorization_header: str, app_version: str):
        bn_payment_header = {
            "Authorization": authorization_header,
            "X-GREE-GAMELIB": f"authVersion%3D{self.auth_version}%26storeType%3D{self.store_type}%26appVersion%3D{app_version}"
                              f"%26uaType%3D{self.uaType}%26carrier%3D{self.carrier}%26compromised%3Dfalse"
                              f"%26countryCode%3D{self.country_code}%26currencyCode%3D{self.currency_code}",

            "User-Agent": f"Mozilla/5.0 (Linux; Android 10; {self.deviceModel} AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36",
            "Content-Type": "application/json; charset=UTF-8",
            "Host": self.host_payment,
            "Accept-Encoding": "gzip",
            "Connection": "keep-alive"
        }
        return bn_payment_header

    def get_bn_moderation_header(self, authorization_header: str, app_version: str):
        bn_moderation_header = {
            "Authorization": authorization_header,
            "X-GREE-GAMELIB": f"authVersion%3D{self.auth_version}%26appVersion%3D{app_version}%26uaType%3D{self.uaType}"
                              f"%26carrier%3D{self.carrier}%26compromised%3Dfalse%26countryCode%3D{self.country_code}"
                              f"%26currencyCode%3D{self.currency_code}",

            "User-Agent": f"Mozilla/5.0 (Linux; Android 10; {self.deviceModel} AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36",
            "Content-Type": "application/json; charset=UTF-8",
            "Host": self.host_moderation,
            "Accept-Encoding": "gzip",
            "Connection": "keep-alive"
        }
        return bn_moderation_header

    def get_device_info_dict(self, app_version: str):
        device_info_dict = {
            "appVersion": app_version,
            "urlParam": None,
            "deviceModel": self.deviceModel,
            "osType": 2,
            "osVersion": "Android OS 10 / API-29",
            "storeType": 2,
            "graphicsDeviceId": 0,
            "graphicsDeviceVendorId": 0,
            "processorCount": 8,
            "processorType": "ARM64 FP ASIMD AES",
            "supportedRenderTargetCount": 8,
            "supports3DTextures": True,
            "supportsAccelerometer": True,
            "supportsComputeShaders": True,
            "supportsGyroscope": True,
            "supportsImageEffects": True,
            "supportsInstancing": True,
            "supportsLocationService": True,
            "supportsRenderTextures": True,
            "supportsRenderToCubemap": True,
            "supportsShadows": True,
            "supportsSparseTextures": True,
            "supportsStencil": 1,
            "supportsVibration": True,
            "uuid": None,
            "xuid": 0,
            "locale": "en_US",
            "numericCountryCode": self.numericCountryCode
        }
        return device_info_dict

class BasicCrypto():
    def __init__(self):
        self.aes = b'E0pBnbdmU9+rLfQ4'

    def encrypt(self, payload):
        packed_request_content = msgpack.packb(payload)
        iv = packed_request_content[0:16]
        padded_request_content = pad(packed_request_content, 16)
        aes = AES.new(self.aes, AES.MODE_CBC, iv)
        encrypted_request_content = aes.encrypt(padded_request_content)
        return iv + encrypted_request_content

    def _decrypt_response(self, response_content):
        iv = response_content[0:16]
        aes = AES.new(self.aes, AES.MODE_CBC, iv)
        pad_text = aes.decrypt(response_content[16:])
        text = unpad(pad_text, 16)
        data_loaded = msgpack.unpackb(text)
        return data_loaded

class BaseAPI():
    URL = "https://api-sinoalice-us.pokelabo.jp"
    EXCESS_TRAFFIC = 14014

    def __init__(self, user_id: int, app_version: str, payment_id: str, prv_key: str, debug = False):
        self.crypto = BasicCrypto()
        self.device_info = DeviceInfo()

        self.request_session = requests.session()
        self.request_session.verify = False
        urllib3.disable_warnings()

        self.oauth_payment = None

        self.uuid = payment_id
        self.priv_key = prv_key

        self.app_id = '859523626835849'

        self.session_id = ''
        self.user_id = user_id
        self.app_version = app_version

        self.mst_version = None

        if debug:
            self.request_session.proxies.update({"http": "127.0.0.1:8080", "https": "127.0.0.1:8080", })
        self.import_key()

    def initialize_payment(self, deviceId: str):
        self.oauth_payment = OAuthPayment(self.device_info, self.priv_key,
                                          deviceId, self.request_session,
                                          self.app_id, self.app_version, self.uuid)

    def set_sessionId(self, ssid: str):
        self.session_id = ssid

    def _login_account(self, uuid: str, x_uid: int):
        inner_payload = self.device_info.get_device_info_dict(self.app_version)
        inner_payload["uuid"] = uuid
        inner_payload["xuid"] = x_uid

        response = self._post("/api/login", inner_payload, remove_header={'Cookie'})
        self.user_id = response["payload"]["userId"]
        self.session_id = response["payload"]["sessionId"]
        return response

    def login(self, deviceId: str, payment_uid: int):
        self.initialize_payment(deviceId)
        self.oauth_payment.payment_authorize()

        self._login_account(None, payment_uid)
        r = self._post("/api/user/get_user_data", {})
        self.oauth_payment.payment_device_verification()
        self.handle_mst()
        return r

    def handle_mst(self):
        this_dir, this_filename = os.path.split(__file__)
        mstDir = os.path.join(this_dir, 'mstList.json')
        with open(mstDir, "r") as f:
            mstList = json.load(f)
        payload = {
            "mstVersionSummaryList": mstList['mstVersionSummaryList']
        }
        r = self._post("/api/mst/check_mst_version", payload)
        self.mst_version = r['payload']['lastCreatedTime']
        if mstList['lastCreatedTime'] != self.mst_version:
            mstList['lastCreatedTime'] = self.mst_version
            for idx, data in enumerate(r['payload']['mstVersionSummaryList']):
                try:
                    tableIndex = next((index for (index, d) in enumerate(mstList['mstVersionSummaryList']) if d['mstTableId'] == data['mstTableId']))
                    mstList['mstVersionSummaryList'][tableIndex] = r['payload']['mstVersionSummaryList'][idx]
                except StopIteration:
                    mstList['mstVersionSummaryList'].append(data)
                    mstList['mstVersionSummaryList'] = sorted(mstList['mstVersionSummaryList'], key=lambda k: k['mstTableId'])
            with open(mstDir, "w") as f:
                mstList = json.dump(mstList, f, indent=4)

    def get_action_time(self, old_action_time=0):
        action_times = [0xfd2c030, 0x18c120b0, 0xdd98840, 0x13ee8a0, 0x1a26560, 0x21526d10, 0xe100190, 0xfbf3830]  # Todo how are those generated
        current_time = (datetime.datetime.utcnow() - datetime.datetime(1,1,1)).total_seconds() * 10**7
        time_offset = random.choice(action_times)
        next_time = int(current_time + time_offset)
        final_time = ((next_time & 0x3FFFFFFFFFFFFFFF) - 0x701CE1722770000)
        return final_time

    def _handle_response(self, response):
        decrypted_response = self.crypto._decrypt_response(response.content)
        logging.debug(f"from {response.request.path_url} {decrypted_response}")
        code = response.status_code

        if decrypted_response.get("errors", None) is not None:
            if decrypted_response["errors"][0]["code"] == BaseAPI.EXCESS_TRAFFIC:
                logging.warning(f"EXCESS_TRAFFIC Exception {response.request.path_url}")
                raise ExcessTrafficException("")

        return decrypted_response

    def sign(self, data, hash_func, key):
        hashed_string = hash_func.new(data)
        base_string = base64.b64encode(hashed_string.digest())
        hashed_string = hash_func.new()
        hashed_string.update(base_string)
        signature = pkcs1_15.new(key).sign(hashed_string)
        return base64.b64encode(signature)

    def import_key(self):
        keyDER = base64.b64decode(self.priv_key)
        self.priv_key = RSA.importKey(keyDER)

    def _prepare_request(self, request_type, resource, inner_payload: dict, remove_header=None):
        self.action_time = self.get_action_time()

        if remove_header is None:
            remove_header = []

        payload = {
            "payload": inner_payload,
            "uuid": self.uuid,
            "userId": self.user_id,
            "sessionId": self.session_id,
            "actionToken": None,
            "ctag": None,
            "actionTime": self.action_time
        }

        logging.debug(f"to {resource} {payload} {self.uuid}")
        payload = self.crypto.encrypt(payload)

        key = self.priv_key
        mac = self.sign(payload, SHA1, key).strip().decode()

        common_headers = {
            "Expect": "100-continue",
            "User-Agent": f"UnityRequest com.nexon.sinoalice {self.app_version} (OnePlus ONEPLUS A5000 Android OS 7.1."
                          f"1 / API-25 (NMF26X/327))",
            "X-post-signature": f"{mac}",
            "X-Unity-Version": "2018.4.19f1",
            "Content-Type": "application/x-msgpack",
            "X-RESOURCE-MST-VERSION": self.mst_version,
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"PHPSESSID={self.session_id}",
            "Host": "api-sinoalice-us.pokelabo.jp"
        }
        for header in remove_header:
            common_headers.pop(header)
        if not self.mst_version:
            common_headers.pop("X-RESOURCE-MST-VERSION")

        self.request_session.headers = common_headers
        return payload

    def _post(self, resource, payload: dict = None, remove_header=None) -> dict:
        url = BaseAPI.URL + resource

        payload = self._prepare_request("POST", resource, payload, remove_header=remove_header)

        resulting_response = None
        timeout_duration = 10 # todo exponential backoff
        while resulting_response is None:
            try:
                response = self.request_session.post(url, payload)
                try:
                    resulting_response = self._handle_response(response)
                except ExcessTrafficException as e:
                    time.sleep(timeout_duration)
                    timeout_duration += 5
                    if timeout_duration > 300:
                        logging.critical(f"Maximum attempts for {resource} aborting")
                        exit(-1)
            except ConnectionError:
                pass
        return resulting_response

class ExcessTrafficException(Exception):
    pass

class API(BaseAPI):

    def POST__api_cleaning_check(self):
        payload = {}
        r = self._post("/api/cleaning/check", payload)
        return r

    def POST__api_cleaning_start(self, cleaning_type=1):
        payload = {
            "cleaningType": cleaning_type
        }
        response = self._post("/api/cleaning/start", payload)

        _data = response["payload"]["cleaningWaveData"]
        enemies = _data["normalEnemyCount"] + _data["rareEnemyCount"]
        wave = _data["nextWave"]
        ap = (_data["normalEnemyCount"] * _data["normalEnemyApRecoveryValue"]) + (_data["rareEnemyCount"] * _data["rareEnemyApRecoveryValue"])
        exp = (_data["normalEnemyCount"] * _data["normalEnemyExpValue"]) + (_data["rareEnemyCount"] * _data["rareEnemyExpValue"])

        return enemies, wave, ap, exp

    def POST__api_cleaning_end_wave(self, remain_time, current_wave, ap, exp, enemy_down):
        payload = {
            "remainTime": remain_time,
            "currentWave": current_wave,
            "getAp": ap,
            "getExp": exp,
            "getEnemyDown": enemy_down
        }
        response = self._post("/api/cleaning/end_wave", payload)

        _data = response["payload"]["cleaningWaveData"]
        enemies = _data["normalEnemyCount"] + _data["rareEnemyCount"]
        wave = _data["nextWave"]

        normalExp = 300 if _data["normalEnemyExpValue"] == 0 else _data["normalEnemyExpValue"]
        rareExp = 3000 if _data["rareEnemyExpValue"] == 0 else _data["rareEnemyExpValue"]

        ap = (_data["normalEnemyCount"] * _data["normalEnemyApRecoveryValue"]) + (_data["rareEnemyCount"] * _data["rareEnemyApRecoveryValue"])
        exp = (_data["normalEnemyCount"] * normalExp) + (_data["rareEnemyCount"] * rareExp)
        level = response["payload"]["userData"]["level"]

        return enemies, wave, ap, exp, level

    def POST__api_cleaning_end(self, end_wave):
        payload = {
            "remainTime": 0,
            "currentWave": end_wave,
            "getAp": 0,
            "getExp": 0,
            "getEnemyDown": 0
        }
        r = self._post("/api/cleaning/end", payload)
        return r

    def POST__api_cleaning_retire(self):
        payload = {}
        self._post("/api/cleaning/retire", payload)

    def POST__api_profile_set_user_title(self, title: int):
        payload = {
            "userTitleMstId": title
        }
        self._post("/api/profile/set_user_title", payload)

    def POST__api_profile_set_comment(self, comment: str):
        payload = {
            "comment": comment
        }
        self._post("/api/profile/set_comment", payload)

    def POST__api_profile_set_user_name(self, username: str):
        payload = {
            "userName": username
        }
        self._post("/api/profile/set_user_name", payload)

    def POST__api_item_shop_expand_max_card_num(self, num: int, _type: int):
        payload = {
            "addNum": num,
            "cardType": _type
        }
        self._post("/api/item_shop/expand_max_card_num", payload)

    def POST__api_gacha_gacha_exec(self, gachaMstId: int, gachaType: int):
        payload = {
            "gachaMstId": gachaMstId,
            "gachaType": gachaType
        }
        self._post("/api/gacha/gacha_exec", payload)

    def POST__api_profile_get_user_name_change_data_list(self):
        payload = {}
        self._post("/api/profile/get_user_name_change_data_list", payload)

    def POST__api_shop_get_royal_user_service(self, checkType: int):
        payload = {
            "checkType": checkType
        }
        self._post("/api/shop/get_royal_user_service", payload)

    def POST__api_costume_get_costumbe_data_list(self):
        payload = {}
        self._post("/api/costume/get_costume_data_list", payload)

    def POST__api_guild_guild_master_migration(self, migratedUserId: int):
        payload = {
            "migratedUserId": migratedUserId
        }
        self._post("/api/guild/guild_master_migration", payload)

    def POST__api_mission_get_mission_reward(self, completedMissionList: list):
        payload = {
            "distributeMstId": completedMissionList
        }
        self._post("/api/mission/get_mission_reward", payload)

    def POST__api_quest_battle_debug_quest_clear(self):
        payload = {}
        self._post("/api/quest_battle/debug_quest_clear?questResult=3", payload)

    def POST__api_gvg_debug_recover_all(self):
        payload = {}
        self._post("/api/gvg/debug_recover_all", payload)

    def POST__api_mst_check_mst_version(self, mstVersionSummaryList: list):
        payload = {
            "mstVersionSummaryList": mstVersionSummaryList
        }
        r = self._post("/api/mst/check_mst_version", payload)
        return r

    def POST__api_gvg_out_battle_get_top(self):
        payload = {}
        r = self._post("/api/gvg_out_battle/get_top", payload)
        return r

    def POST__api_gvg_out_battle_get_result(self, gvgDataId: int):
        payload = {
            "gvgDataId": gvgDataId
        }
        r = self._post("/api/gvg_out_battle/get_result", payload)
        return r

    def POST__api_gvg_out_battle_get_battle_history(self, gvgDataId: int, pageNo: int, type: int):
        payload = {
            "gvgDataId": gvgDataId,
            "pageNo": pageNo,
            "type": type
        }
        r = self._post("/api/gvg_out_battle/get_battle_history", payload)
        return r

    def POST__api_quest_get_stage_data(self, questStageMstId: int):
        payload = {
            "questStageMstId": questStageMstId
        }
        r = self._post("/api/quest/get_stage_data", payload)
        return r

    def POST__api_quest_get_stage_reward(self, questStageMstId: int):
        payload = {
            "questStageMstId": questStageMstId
        }
        r = self._post("/api/quest/get_stage_reward", payload)
        return r

    def POST__api_deck_get_deck_data_list(self):
        payload = {}
        r = self._post("/api/deck/get_deck_data_list", payload)
        return r

    def POST__api_quest_check_quest_event(self, questStageMstId: int):
        payload = {
            "questStageMstId": questStageMstId
        }
        r = self._post("/api/quest/check_quest_event", payload)
        return r

    def POST__api_quest_battle_initialize_stage(self, deckDataId: int, joinStatus: int, joinType: int, questStageMstId: int):
        payload = {
            "deckDataId": deckDataId,
            "joinStatus": joinStatus,
            "joinType": joinType,
            "questStageMstId": questStageMstId
        }
        r = self._post("/api/quest_battle/initialize_stage", payload)
        return r

    def POST__api_quest_battle_get_info(self):
        payload = {}
        r = self._post("/api/quest_battle/get_info", payload)
        return r

    def POST__api_quest_battle_get_art_list(self):
        payload = {}
        r = self._post("/api/quest_battle/get_art_list", payload)
        return r

    def POST__api_quest_battle_get_current_deck_data(self):
        payload = {}
        r = self._post("/api/quest_battle/get_current_deck_data", payload)
        return r

    def POST__api_quest_battle_change_ai_mode(self, isAi: int):
        payload = {
            "isAi": isAi
        }
        r = self._post("/api/quest_battle/change_ai_mode", payload)
        return r

    def POST__api_quest_battle_wave_start(self, currentQuestWaveMstId: int):
        payload = {
            "currentQuestWaveMstId": currentQuestWaveMstId
        }
        r = self._post("/api/quest_battle/wave_start", payload)
        return r

    def POST__api_quest_battle_wave_clear(self, currentQuestWaveMstId: int):
        payload = {
            "currentQuestWaveMstId": currentQuestWaveMstId
        }
        r = self._post("/api/quest_battle/wave_clear", payload)
        return r

    def POST__api_quest_battle_finalize_stage_for_user(self):
        payload = {}
        r = self._post("/api/quest_battle/finalize_stage_for_user", payload)
        return r

    def POST__api_quest_get_result(self, questDataId: int):
        payload = {
            "questDataId": questDataId
        }
        r = self._post("/api/quest/get_result", payload)
        return r

    def POST__api_guild_guild_data(self):
        payload = {}
        r = self._post("/api/guild/guild_data", payload)
        return r

    def POST__api_guild_guild_member_list(self, guildDataId: int):
        payload = {
            "guildDataId": guildDataId
        }
        r = self._post("/api/guild/guild_member_list", payload)
        return r

    def POST__api_gvg_event_get_main_battle_guild_list(self, leagueId: int, pageNo: int):
        payload = {
            "leagueId": leagueId,
            "pageNo": pageNo
        }
        r = self._post("/api/gvg_event/get_main_battle_guild_list", payload)
        return r

    def POST__api_gvg_event_get_gvg_event_ranking(self, guildDataId: int, gvgTimeType: int, leagueId: int, pageNo: int):
        payload = {
            "guildDataId": guildDataId,
            "gvgTimeType": gvgTimeType,
            "leagueId": leagueId,
            "pageNo": pageNo
        }
        r = self._post("/api/gvg_event/get_gvg_event_ranking", payload)
        return r

    def POST__api_gvg_event_get_bookie_list(self):
        payload = {}
        r = self._post("/api/gvg_event/get_bookie_list", payload)
        return r

    def POST__api_gvg_event_get_bookie_result(self):
        payload = {}
        r = self._post("/api/gvg_event/get_bookie_result", payload)
        return r

    def POST__api_item_get_boost_item(self):
        payload = {}
        r = self._post("/api/item/get_boost_item", payload)
        return r

    def POST__api_profile_get_alice_target_profile_data(self, targetUserId: int):
        payload = {
            "targetUserId": targetUserId
        }
        r = self._post("/api/profile/get_alice_target_profile_data", payload)
        return r

    def POST__api_profile_get_target_profile_data(self, targetUserId: int):
        payload = {
            "targetUserId": targetUserId
        }
        r = self._post("/api/profile/get_target_profile_data", payload)
        return r

    def POST__api_user_get_user_data(self, userId: int):
        payload = {
            "userId": userId
        }
        r = self._post("/api/user/get_user_data", payload)
        return r

    def POST__api_deck_deck_copy_fact(self, deckDataId: int):
        payload = {
            "deckDataId": deckDataId
        }
        r = self._post("/api/deck/deck_copy_fact", payload)
        return r

    def POST__api_deck_deck_rename_fact(self, deckDataId: int, deckName: str):
        payload = {
            "deckDataId": deckDataId,
            "deckName": deckName
        }
        r = self._post("/api/deck/deck_rename_fact", payload)
        return r

    def POST__api_deck_deck_delete_fact(self, deckDataIds: list):
        payload = {
            "deckDataIds": deckDataIds
        }
        r = self._post("/api/deck/deck_delete_fact", payload)
        return r

    def POST__api_deck_get_deck_detail_data(self, deckDataId: int):
        payload = {
            "deckDataId": deckDataId
        }
        r = self._post("/api/deck/get_deck_detail_data", payload)
        return r

    def POST__api_quest_get_alice_stage_list(self, battleNum: int, questAreaMstId: int):
        payload = {
            "battleNum": battleNum,
            "questAreaMstId": questAreaMstId
        }
        r = self._post("/api/quest/get_alice_stage_list", payload)
        return r

    def POST__api_quest_quest_skip(self, amount: int, deckDataId: int, questStageMstId: int, useItemMstId: int):
        payload = {
            "amount": amount,
            "deckDataId": deckDataId,
            "questStageMstId": questStageMstId,
            "useItemMstId": useItemMstId
        }
        r = self._post("/api/quest/quest_skip", payload)
        return r

    def POST__api_card_evo_evolution(self, baseCardDataId: int):
        payload = {
            "baseCardDataId": baseCardDataId
        }
        r = self._post("/api/card_evo/evolution", payload)
        return r

    def POST__api_gacha_get_shooting_gacha_top(self):
        payload = {}
        r = self._post("/api/gacha/get_shooting_gacha_top", payload)
        return r

    def POST__api_gacha_shooting_gacha_exec(self, probabilityId: int, shootingGachaMstId: int):
        payload = {
            "probabilityId": probabilityId,
            "shootingGachaMstId": shootingGachaMstId
        }
        r = self._post("/api/gacha/shooting_gacha_exec", payload)
        return r

    def POST__api_present_get_present_data(self):
        payload = {}
        r = self._post("/api/present/get_present_data", payload)
        return r

    def POST__api_present_gain_present(self, presentDataId: list, sendCardStorageFlag: bool):
        payload = {
            "presentDataId": presentDataId,
            "sendCardStorageFlag": sendCardStorageFlag
        }
        r = self._post("/api/present/gain_present", payload)
        return r

    def POST__api_my_page_get_my_page_info_for_alice_11(self):
        payload = {}
        r = self._post("/api/my_page/get_my_page_info_for_alice_11", payload)
        return r

    def POST__api_item_set_multi_boost_item(self, itemMstIds: list, overEffectType: int):
        payload = {
            "itemMstIds": itemMstIds,
            "overEffectType": overEffectType
        }
        r = self._post("/api/item/set_multi_boost_item", payload)
        return r

    def POST__api_item_get_item_data_list(self):
        payload = {}
        r = self._post("/api/item/get_item_data_list", payload)
        return r

    def POST__api_ranking_guild_ranking(self, countryCode: int, mode: int, pageNo: int, rank: int, _type: int):
        payload = {
            "countryCode": countryCode,
            "mode": mode,
            "pageNo": pageNo,
            "rank": rank,
            "type": _type
        }
        r = self._post("/api/ranking/guild_ranking", payload)
        return r

    #######

    def POST__api_mst_get_mst_list(self, mstList: str, mstTableId: int, isBackgroundConnection: bool = False) -> dict:
        payload = {
            "mstTableId": mstTableId,
            "isBackgroundConnection": isBackgroundConnection
        }
        url = 'get_' + mstList + '_mst_list'
        r = self._post("/api/mst/" + url, payload)
        return r