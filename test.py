from database import Database

db = Database()

dept_code_dict = {
    "D001": "내과", "D002": "소아청소년과", "D003": "신경과", "D004": "정신건강의학과", "D005": "피부과", "D006": "외과",
    "D007": "흉부외과",
    "D008": "정형외과", "D009": "신경외과", "D010": "성형외과", "D011": "산부인과", "D012": "안과", "D013": "이비인후과",
    "D014": "비뇨기과",
    "D016": "재활의학과",
    "D017": "마취통증의학과", "D018": "영상의학과", "D019": "치료방사선과", "D020": "임상병리과", "D021": "해부병리과", "D022": "가정의학과",
    "D023": "핵의학과", "D024": "응급의학과", "D026": "치과", "D034": "구강악안면외과"
}

dept_name_dict = {v: k for k, v in dept_code_dict.items()}
sql = "select * from Disease"

sql_result = db.executeAll(sql)
medical_dept_list = []
for result in sql_result:

    result_split = result['medical_dept_name'].split(',')
    # split medical_dept_name
    dept_code = []
    for medical_dept in result_split:
        # dept name 에 있을 경우
        if medical_dept in dept_name_dict:
            select = dept_name_dict[medical_dept]
        else:
            if "내과" in medical_dept or "암" in medical_dept:
                select = dept_name_dict["내과"]
            elif "외과" in medical_dept:
                select = (dept_name_dict["외과"])

            elif "신경" in medical_dept:
                select = (dept_name_dict["신경과"])

            elif "소아" in medical_dept or "어린이" in medical_dept or "신생아과" in medical_dept:
                select = dept_name_dict["소아청소년과"]

            elif "비뇨의학과" in medical_dept:
                select = dept_name_dict["비뇨기과"]

        if select not in dept_code:
            dept_code.append(select)
        medical_dept_code = ",".join(dept_code)

        sql = f"UPDATE Disease SET medical_dept_code=\"{medical_dept_code}\" where id = \"{result['id']}\";"
        print(sql)
        db.execute(sql)
        db.commit()