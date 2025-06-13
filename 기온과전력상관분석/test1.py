import pandas as pd

# CSV 파일 불러오기
df = pd.read_csv("서울_전력사용량_2022_2024.csv", encoding="utf-8-sig")

# 컬럼명 앞뒤 공백 제거 (혹시라도 있을 경우 대비)
df.columns = df.columns.str.strip()

# 문자열 쉼표 제거 + 띄어쓰기 나눠서 숫자 합산
def parse_sum(s):
    parts = s.split()  # "1,234 2,345" → ["1,234", "2,345"]
    nums = [int(p.replace(",", "")) for p in parts]
    return sum(nums)

# ✅ 여기서 컬럼명 "사용량(kWh)"로 정확히 사용
df["사용량(kWh)"] = df["사용량(kWh)"].apply(parse_sum)

# 날짜 컬럼 변환
df["월"] = pd.to_datetime(df["월"])

print(df.head())
# 전처리 완료된 데이터 저장
df.to_csv("전처리완료_전력사용량.csv", index=False, encoding="utf-8-sig")
print("전처리 완료된 데이터가 '전처리완료_전력사용량.csv'로 저장되었습니다.")