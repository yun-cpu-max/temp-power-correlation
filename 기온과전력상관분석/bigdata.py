import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import calendar
import numpy as np
import matplotlib.font_manager as fm



# 🔹 1. 전력 사용량 데이터 로드 및 전처리
power_df = pd.read_csv("전처리완료_전력사용량.csv", encoding="utf-8-sig")
power_df["월"] = pd.to_datetime(power_df["월"])
power_df.rename(columns={"사용량(kWh)": "전력사용량"}, inplace=True)

# 🔹 2. 기온 API 요청 함수 (일자료를 가져와 월별 평균 계산)
def get_daily_and_avg_monthly_temp(start_year_month_day, end_year_month_day, service_key):
    url = 'http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList'
    
    params = {
        'serviceKey' : service_key,
        'pageNo' : '1',
        'numOfRows' : '999',
        'dataType' : 'JSON',
        'dataCd' : 'ASOS',
        'dateCd' : 'DAY',
        'startDt' : start_year_month_day,
        'endDt' : end_year_month_day,
        'stnIds' : '108' # 서울
    }
    
    res = requests.get(url, params=params)

    try:
        json_data = res.json()
        
        result_code = json_data["response"]["header"]["resultCode"]
        result_msg = json_data["response"]["header"]["resultMsg"]
        
        if result_code != "00":
            print(f"API 오류 발생: 코드 {result_code}, 메시지: {result_msg}")
            return pd.DataFrame()
            
        if "items" not in json_data["response"]["body"] or not json_data["response"]["body"]["items"]["item"]:
            print("API 응답에 데이터(item)가 없습니다.")
            return pd.DataFrame()

        items = json_data["response"]["body"]["items"]["item"]
        df = pd.DataFrame(items)
        
        df["날짜"] = pd.to_datetime(df["tm"], format='%Y-%m-%d')
        
        df["평균기온"] = pd.to_numeric(df["avgTa"], errors='coerce') 
        df = df.dropna(subset=['평균기온'])
        
        if df.empty:
            print("변환 후 유효한 평균기온 데이터가 없습니다.")
            return pd.DataFrame()

        df["월"] = df["날짜"].dt.to_period('M').dt.to_timestamp()
        monthly_avg_temp_df = df.groupby('월')['평균기온'].mean().reset_index()
        
        return monthly_avg_temp_df[["월", "평균기온"]]

    except Exception as e:
        print("JSON 파싱 또는 데이터 처리 오류:", e)
        print("최종 응답 내용:", res.text)
        return pd.DataFrame()

# 🔹 3. 기온 데이터 불러오기 (2023 ~ 2024)
service_key = "GsHjiIoNIyD9oVMYcbPe3TYBoVpraJ5uSAOCz2ItBGZF+qTlgYkEx5GBHOPDIF7D5TXAlORQ15eUBM/9fJxiAw=="

all_monthly_temp_df = pd.DataFrame()
start_year = 2022
end_year = 2024

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, calendar.monthrange(year, month)[1])
        
        start_dt_str = start_date.strftime('%Y%m%d')
        end_dt_str = end_date.strftime('%Y%m%d')

        monthly_temp_data = get_daily_and_avg_monthly_temp(start_dt_str, end_dt_str, service_key)
        
        if not monthly_temp_data.empty:
            all_monthly_temp_df = pd.concat([all_monthly_temp_df, monthly_temp_data], ignore_index=True)

if not all_monthly_temp_df.empty:
    all_monthly_temp_df = all_monthly_temp_df.drop_duplicates(subset='월').sort_values(by='월').reset_index(drop=True)
else:
    print("모든 API 호출에서 유효한 기온 데이터를 가져오지 못했습니다. API 응답 로그를 확인하세요.")
    exit()

temp_df = all_monthly_temp_df

# 🔹 4. 전력 사용량과 기온 데이터 병합
merged_df = pd.merge(power_df, temp_df, on="월")

# 🔹 5. 다항 회귀 분석
merged_df['평균기온_제곱'] = merged_df['평균기온']**2

X = merged_df[["평균기온", "평균기온_제곱"]]
y = merged_df["전력사용량"]

# 데이터 분할 (예: 80% 학습, 20% 테스트)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

# 훈련 데이터 R²
train_r2 = model.score(X_train, y_train)
# 테스트 데이터 R²
test_r2 = model.score(X_test, y_test)

print(f"훈련 R²: {train_r2:.3f}")
print(f"테스트 R²: {test_r2:.3f}")

y_pred = model.predict(X)

r2 = r2_score(y, y_pred)
print(f"다항 회귀 R²: {r2:.3f}")

# 🔹 6. 시각화 (다항 회귀 곡선 반영)

plt.figure(figsize=(10, 6))
sns.set_theme(style="whitegrid")
font_path = "C:/Windows/Fonts/malgun.ttf"
fontprop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = fontprop.get_name()
plt.rcParams['axes.unicode_minus'] = False
sns.scatterplot(x="평균기온", y="전력사용량", data=merged_df, label='실제 데이터')

min_temp = merged_df['평균기온'].min()
max_temp = merged_df['평균기온'].max()
temp_range = pd.DataFrame({'평균기온': np.linspace(min_temp, max_temp, 100)})
temp_range['평균기온_제곱'] = temp_range['평균기온']**2
pred_power = model.predict(temp_range)

plt.plot(temp_range['평균기온'], pred_power, color='red', linestyle='--', label=f'다항 회귀선 (R²={r2:.3f})')

plt.text(x=min_temp, y=y.max()*0.95, s=f"R² = {r2:.3f}", fontsize=12, color="black")

plt.title("서울 월별 평균기온 vs 전력사용량\n(다항회귀 & 산점도 시각화)", fontsize=14)
plt.xlabel("평균기온 (°C)", fontsize=12)
plt.ylabel("전력사용량 (kWh)", fontsize=12)
plt.legend()
plt.tight_layout()
plt.show()