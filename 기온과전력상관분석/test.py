import pandas as pd
from glob import glob

files = ["2022_1.xls","2022_2.xls","2023_1.xls", "2023_2.xls", "2024_1.xls", "2024_2.xls"]
df_list = []

for file in files:
    try:
        df = pd.read_excel(file, skiprows=4)
        print(f"\n--- File: {file} ---")
        print("Loaded Columns:", df.columns.tolist()) # 리스트 형태로 출력
        print("--------------------")

        # 여기에서 '시군구' 열의 존재 여부와 정확한 이름을 확인하세요
        if '시군구' in df.columns:
            print("'시군구' 열이 데이터프레임에 있습니다.")
        else:
            print("'시군구' 열이 데이터프레임에 없습니다. 실제 열 이름을 확인하세요.")
            # 어떤 다른 열 이름들이 있는지 확인해보기 (예: 'Unnamed: 1' 등)
            # 혹은 다른 이름으로 된 '시군구'와 유사한 열이 있는지 찾아보기
            
        # 다음 줄에서 에러가 발생하므로, 정확한 열 이름을 확인하고 수정해야 합니다.
        df = df[df["시군구"] == "전체(시 / 군 / 구)"]
        df = df[df["계약구분"].isin(["주택용", "일반용"])]
        df["월"] = pd.to_datetime(df["년월"].astype(str), format="%Y%m")
        df_list.append(df[["월", "사용량(kWh)"]])
    
    except KeyError as e:
        print(f"File: {file} 에서 KeyError 발생: {e}")
        print("현재 로드된 열 이름:", df.columns.tolist() if 'df' in locals() else "N/A")
        print("엑셀 파일의 열 이름과 skiprows 설정을 다시 확인해주세요.")
        break # 에러가 발생하면 다음 파일 처리를 중단하고 진단에 집중
    except Exception as e:
        print(f"File: {file} 처리 중 예상치 못한 에러 발생: {e}")
        break

if not df_list: # df_list가 비어있으면 데이터 처리 실패
    print("데이터프레임이 성공적으로 로드되지 않아 병합할 수 없습니다.")
else:
    # 병합 후 월별 총합
    merged_df = pd.concat(df_list)
    monthly_total = merged_df.groupby("월")["사용량(kWh)"].sum().reset_index()

    # CSV로 저장
    monthly_total.to_csv("서울_전력사용량_2022_2024.csv", index=False, encoding="utf-8-sig")