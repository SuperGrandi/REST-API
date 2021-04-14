import requests
import xmltodict
import json
import googlemaps
from haversine import haversine

"""
QZ : B:병원, C:의원

QD : 진료과목
D001:내과, D002:소아청소년과, D003:신경과, D004:정신건강의학과, D005:피부과, D006:외과, D007:흉부외과, 
D008:정형외과, D009:신경외과, D010:성형외과, D011:산부인과, D012:안과, D013:이비인후과, D014:비뇨기과, D016:재활의학과, 
D017:마취통증의학과, D018:영상의학과, D019:치료방사선과, D020:임상병리과, D021:해부병리과, D022:가정의학과, 
D023:핵의학과, D024:응급의학과, D026:치과, D034:구강악안면외과

"""


def get_hospital_by_code():
    Q0 = "서울특별시"
    Q1 = "광진구"
    QZ = "C"
    QD = "D001"

    res = requests.get(
        url="http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlMdcncListInfoInqire",
        params={
            'serviceKey': 'LV05BMRXXZ0XCU+yhvN+kdVE/LORIjoi1sFvkiZf007DUxd04F77IbYEfVySm62z3JKNyFz30EKI2K3rlORW0g==',
            'Q0': Q0,
            "Q1": Q1,
            "QZ": QZ,
            'QD': QD,
        }
    )
    jsonString = json.dumps(xmltodict.parse(res.text), indent=4, ensure_ascii=False)
    # print(jsonString)


def get_hospital_info(hospital_id):
    res = requests.get(
        url="http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlBassInfoInqire",
        params={
            'serviceKey': 'LV05BMRXXZ0XCU+yhvN+kdVE/LORIjoi1sFvkiZf007DUxd04F77IbYEfVySm62z3JKNyFz30EKI2K3rlORW0g==',
            'HPID': hospital_id,
        }
    )
    return xmltodict.parse(res.text)


def get_hospital_by_location(lat,lon, dept_code, distance):
    dept_code_dict = {
        "D001": "내과", "D002": "소아청소년과", "D003": "신경과", "D004": "정신건강의학과", "D005": "피부과", "D006": "외과", "D007": "흉부외과",
        "D008": "정형외과", "D009": "신경외과", "D010": "성형외과", "D011": "산부인과", "D012": "안과", "D013": "이비인후과", "D014": "비뇨기과",
        "D016": "재활의학과",
        "D017": "마취통증의학과", "D018": "영상의학과", "D019": "치료방사선과", "D020": "임상병리과", "D021": "해부병리과", "D022": "가정의학과",
        "D023": "핵의학과", "D024": "응급의학과", "D026": "치과", "D034": "구강악안면외과"
    }
    dept_name = dept_code_dict[dept_code]

    result = {}
    print("Load Data")
    res = requests.get(
        url="http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlMdcncLcinfoInqire",
        params={
            'serviceKey': 'LV05BMRXXZ0XCU+yhvN+kdVE/LORIjoi1sFvkiZf007DUxd04F77IbYEfVySm62z3JKNyFz30EKI2K3rlORW0g==',
            "WGS84_LAT": lat,  # 위도
            "WGS84_LON": lon,  # 경도
            "numOfRows": 50,
        }
    )
    print(res.elapsed.total_seconds())

    print("Parse Data")
    result_dict = xmltodict.parse(res.text)
    result_code = result_dict["response"]["header"]['resultCode']
    result['result_code'] = result_code
    items = result_dict["response"]["body"]["items"]["item"]

    for item in items:
        if item['dutyDiv'] in ['G', 'R']:
            continue

        if distance < float(item['distance']) * 1000:
            break


        hos_info = get_hospital_info(item['hpid'])
        hos_info = hos_info["response"]["body"]['items']['item']['dgidIdName'].split(',')

        if dept_name in hos_info:
            print("병원명:", item['dutyName'] + " (" + item['dutyDiv'] + ")")
            print("주소:", item['dutyAddr'])
            print("진료과목:", hos_info)
            print("거리:", int(float(item['distance']) * 1000))
            print("진료시간:", item['startTime'], "~", item['endTime'])
            print()


if __name__ == '__main__':
    get_hospital_by_location("37.55711127134004", "127.08067617045535", "D001", 300)
