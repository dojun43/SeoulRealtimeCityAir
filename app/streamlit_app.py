from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime
from datetime import date
from plots import make_map, make_donut 

################### execute query
def execute_query(query):
    load_dotenv()

    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_CUSTOM_USER')}:" 
        f"{os.getenv('POSTGRES_CUSTOM_PASSWORD')}@{os.getenv('HOST')}:"
        f"{os.getenv('POSTGRES_CUSTOM_PORT')}/{os.getenv('POSTGRES_CUSTOM_DBNAME')}"
    )
    
    df = pd.read_sql_query(query, engine)

    return df 

################### function 
def get_air_quality_level(value, air):
    air_quality_thresholds = {
    'PM25': [(16, '좋음'), (36, '보통'), (76, '나쁨'), (float('inf'), '매우나쁨')],
    'PM10': [(31, '좋음'), (81, '보통'), (151, '나쁨'), (float('inf'), '매우나쁨')],
    'O3': [(0.031, '좋음'), (0.091, '보통'), (0.151, '나쁨'), (float('inf'), '매우나쁨')],
    'NO2': [(0.031, '좋음'), (0.061, '보통'), (0.201, '나쁨'), (float('inf'), '매우나쁨')],
    'CO': [(2.01, '좋음'), (9.01, '보통'), (15.01, '나쁨'), (float('inf'), '매우나쁨')],
    'SO2': [(0.021, '좋음'), (0.051, '보통'), (0.151, '나쁨'), (float('inf'), '매우나쁨')],
    'IDEX_MVL': [(51, '좋음'), (101, '보통'), (251, '나쁨'), (float('inf'), '매우나쁨')],
    }

    thresholds = air_quality_thresholds[air]

    for threshold, level in thresholds:
        if value < threshold:
            return level
        
    return thresholds[-1][1]

def create_region_air_df(selected_date, selected_time, selected_region):
    query = f'''
            SELECT * 
            FROM "RealtimeCityAir_{selected_date}"
            WHERE "MSRDT" = {selected_time}
                    AND "MSRSTE_NM" = '{selected_region}'
            '''
    df = execute_query(query)
    
    air_level_list = []

    for air in ['PM10','PM25', 'O3', 'NO2', 'CO', 'SO2', 'IDEX_MVL']:
        value = df[air].iloc[0]
        air_level_list.append(get_air_quality_level(value, air))

    data = {
            '대기': [
                    '미세먼지(PM-10)',
                    '초미세먼지(PM-25)',
                    '오존(O3)', 
                    '이산화질소(NO2)', 
                    '일산화탄소(CO)',
                    '아황산가스(SO2)',
                    '통합대기환경지수'],
            '수치': [str(df.PM10.iloc[0]) + '㎍/㎥', 
                    str(df.PM25.iloc[0]) + '㎍/㎥', 
                    str(df.O3.iloc[0]) + 'ppm', 
                    str(df.NO2.iloc[0]) + 'ppm', 
                    str(df.CO.iloc[0]) + 'ppm',
                    str(df.SO2.iloc[0]) + 'ppm',
                    str(df.IDEX_MVL.iloc[0])],
            '대기질 지수': air_level_list
        }
    region_air_df = pd.DataFrame(data)

    return region_air_df

################### Page configuration
st.set_page_config(
    page_title="서울시 대기환경 현황",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")


################### Sidebar
with st.sidebar:
    st.title('서울시 대기환경 현황')
    
    # 대기 선택
    air_list = ['미세먼지(PM-10)','초미세먼지(PM-2.5)','오존(O3)']
        
    selected_air = st.selectbox('대기 선택', 
                                air_list, 
                                index=0 # 기본값 index
                                )

    # 지역구 선택
    region_list = ['중구', '강남구', '강동구', '강북구', '강서구', '관악구', 
                '광진구', '구로구', '금천구', '노원구', '도봉구', '동작구', 
                '마포구', '서초구', '성동구', '성북구', '송파구', '양천구', 
                '용산구', '은평구', '종로구', '중랑구', '동대문구', '서대문구', 
                '영등포구']
        
    selected_region = st.selectbox('지역구 선택', 
                                   region_list, 
                                   index=0 # 기본값 index
                                   )

    # 날짜 선택 
    selected_date = st.date_input('날짜 선택', 
                                  value=date.today(), # 기본값
                                  min_value=date(2024, 9, 15),  
                                  max_value=date.today()
                                )
    
    # 시간 선택
    query = f'''
        SELECT DISTINCT "MSRDT"
        FROM "RealtimeCityAir_{selected_date}"
        ORDER BY "MSRDT" 
        '''
    df = execute_query(query)
    df['MSRDT'] = pd.to_datetime(df['MSRDT'], format='%Y%m%d%H%M')
    
    time_list = list(df.MSRDT.dt.strftime('%H:%M')) # 시:분 추출
    
    selected_time = st.selectbox('시간 선택', 
                                   time_list, 
                                   index=len(time_list)-1 # 기본값 index
                                   )
    
    date_obj = datetime.strptime(str(selected_date), '%Y-%m-%d')
    time_obj = datetime.strptime(str(selected_time), '%H:%M')

    selected_time = date_obj.replace(hour=time_obj.hour, minute=time_obj.minute)
    selected_time = selected_time.strftime('%Y%m%d%H%M')


################### Dashboard Main Panel
col = st.columns((4, 2.5), gap='medium')

with col[0]:
    # 도넛 차트 생성
    st.markdown(f'### 서울시 평균')

    update_date = datetime.strptime(selected_time, "%Y%m%d%H%M")
    update_date = update_date.strftime("%Y년 %m월 %d일 %H시")
    st.write(f"{update_date}")

    sub_col = st.columns((1, 1, 1, 2), gap='medium')

    query = f'''
        SELECT AVG("PM10") AS PM10,
               AVG("PM25") AS PM25,
               AVG("O3") AS O3,
               AVG("IDEX_MVL") AS IDEX_MVL
        FROM "RealtimeCityAir_{selected_date}"
        WHERE "MSRDT" = {selected_time}
        '''
    df = execute_query(query)

    with sub_col[0]:
        title = '미세먼지'
        input_value = df["pm10"].iloc[0]
        input_ratio = input_value / 150 * 100 
        input_status = get_air_quality_level(input_value, 'PM10') 

        if input_ratio > 100:
            input_ratio = 100

        donut_chart = make_donut(title, input_value, input_ratio, input_status)
        st.altair_chart(donut_chart)

    with sub_col[1]:
        title = '초미세먼지'
        input_value = df["pm25"].iloc[0]
        input_ratio = input_value / 75 * 100 
        input_status = get_air_quality_level(input_value, 'PM25') 

        if input_ratio > 100:
            input_ratio = 100

        donut_chart = make_donut(title, input_value, input_ratio, input_status)
        st.altair_chart(donut_chart)

    with sub_col[2]:
        title = '오존'
        input_value = round(df["o3"].iloc[0], 4)
        input_ratio = input_value / 0.15 * 100 
        input_status = get_air_quality_level(input_value, 'O3') 

        if input_ratio > 100:
            input_ratio = 100

        donut_chart = make_donut(title, input_value, input_ratio, input_status)
        st.altair_chart(donut_chart)

    with sub_col[3]:
        title = '통합대기환경지수'
        input_value = df["idex_mvl"].iloc[0]
        input_ratio = input_value / 250 * 100 
        input_status = get_air_quality_level(input_value, 'IDEX_MVL') 

        if input_ratio > 100:
            input_ratio = 100

        donut_chart = make_donut(title, input_value, input_ratio, input_status)
        st.altair_chart(donut_chart)

    # 지역구 별 map 시각화
    air_code_dict = {'미세먼지(PM-10)' : 'PM10',
                    '초미세먼지(PM-2.5)' : 'PM25', 
                     '오존(O3)' : 'O3',
                     } 
    selected_air_code = air_code_dict[selected_air]

    st.markdown(f'#### {selected_air}')

    update_date = datetime.strptime(selected_time, "%Y%m%d%H%M")
    update_date = update_date.strftime("%Y년 %m월 %d일 %H시")
    st.write(f"{update_date}")

    query = f'''
        SELECT * 
        FROM "RealtimeCityAir_{selected_date}"
        WHERE "MSRDT" = {selected_time}
        '''
    df = execute_query(query)

    make_map(df, 'MSRSTE_NM', selected_air_code)


with col[1]:
    st.markdown(f'#### {selected_region} 대기질 정보')

    update_date = datetime.strptime(selected_time, "%Y%m%d%H%M")
    update_date = update_date.strftime("%Y년 %m월 %d일 %H시")
    st.write(f"{update_date}")

    # 지역구 별 대기질 정보
    df = create_region_air_df(selected_date, selected_time, selected_region)

    st.dataframe(
    df,
    column_order=("대기", "수치", "대기질 지수"),
    hide_index=True,
    column_config={
        "대기": st.column_config.TextColumn(
            "대기",
        ),
        "수치": st.column_config.TextColumn(
            "수치",
        ),
        "대기질 지수": st.column_config.TextColumn(
            "대기질 지수",
        )
    })

    # 시간별 미세먼지(PM-10)
    query = f'''
            SELECT * 
            FROM "RealtimeCityAir_{selected_date}"
            WHERE "MSRSTE_NM" = '{selected_region}'
            '''
    df = execute_query(query)
    df['MSRDT'] = pd.to_datetime(df['MSRDT'], format='%Y%m%d%H%M')

    bar_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('MSRDT', title='시간'),
        y=alt.Y('PM10', title='미세먼지 (㎍/㎥)', scale=alt.Scale(domain=[0, 150]))
    ).properties(
        title='시간별 미세먼지(PM-10)',
        width=350,
        height=300
    )

    st.altair_chart(bar_chart)

    # 시간별 초미세먼지(PM-25)

    bar_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('MSRDT', title='시간'),
        y=alt.Y('PM25', title='초미세먼지 (㎍/㎥)', scale=alt.Scale(domain=[0, 150]))
    ).properties(
        title='시간별 초미세먼지(PM-25)',
        width=350,
        height=300
    )

    st.altair_chart(bar_chart)