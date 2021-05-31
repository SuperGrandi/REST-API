import operator

from database import Database

db = Database()

sql = """
    SELECT *
    FROM  Symptom  
"""
symptom_table = db.executeAll(sql)

# Init Symptom Table part_code
sql = """
    UPDATE Symptom 
    SET part_code = NULL 
"""
db.execute(sql)
db.commit()

sql = """
    SELECT * 
    FROM  Disease
    """

disease_table = db.executeAll(sql)
part_code = {row['symptom_code']: {row['part_code']: 0 for row in disease_table} for row in symptom_table}

for row in disease_table:
    symptom_code_list = list(row['symptom_code'].split(','))

    for code in symptom_code_list:
        if code in ["", "S"]:
            continue
        part_code[code][row['part_code']] += 1

for symptom_code, count in part_code.items():
    print(symptom_code)
    sum_count = sum(count.values())
    if sum_count == 0:
        continue
    sort_item = dict(sorted(count.items(), key=operator.itemgetter(1), reverse=True))

    # 50% 이상만
    WEIGHT = 0.5

    filted_list = dict(filter(lambda x: x[1] / sum_count >= WEIGHT, sort_item.items()))

    sql = """
    UPDATE Symptom 
    SET part_code = %s 
    WHERE symptom_code = %s 
    """

    if filted_list:
        db.execute(sql, (list(filted_list)[0], symptom_code))
        db.commit()
