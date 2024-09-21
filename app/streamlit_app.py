from dotenv import load_dotenv
import os
import psycopg2
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json
import folium
from streamlit_folium import folium_static
import branca
from shapely.geometry import shape, mapping

# Connection DB
def execute_query(query):
    load_dotenv()

    conn = psycopg2.connect(
        host=os.getenv('HOST'),          
        database=os.getenv('POSTGRES_CUSTOM_DBNAME'),  
        user=os.getenv('POSTGRES_CUSTOM_USER'),          
        password=os.getenv('POSTGRES_CUSTOM_PASSWORD'),
        port=os.getenv('POSTGRES_CUSTOM_PORT')  
    )
    
    df = pd.read_sql_query(query, conn)

    conn.close()

    return df 

################### Page configuration
st.set_page_config(
    page_title="서울시 대기환경 현황",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")


################### Sidebar
with st.sidebar:
    st.title('서울시 대기환경 현황')
    
    air_list = ['PM10', 'PM25', 'O3']
    
    selected_air = st.selectbox('미세먼지 종류', air_list, index=len(air_list)-1)

    # query = 'SELECT DISTINCT "MSRDT" \
    #      FROM "RealtimeCityAir_2024-09-15"'
    # df = execute_query(query)

    # date_list = list(df.MSRDT)
    
    # selected_date = st.selectbox('Select a date', date_list, index=len(date_list)-1)

################### Plots
def make_choropleth(input_df, input_id, input_column):
    # GeoJSON 파일 읽기
    geo_data = 'seoul_geo_gu.json'
    with open(geo_data, encoding='utf-8') as f:
        geo_json_data = json.load(f)
    
    # 중심 좌표 설정
    center = [37.567, 126.986]
    m = folium.Map(location=center, zoom_start=10.5)

    # Custom colormap 설정
    bins = [0, 15, 35, 75, 300]
    colors = ['#5C8CDD', '#65B24B', '#E2D058', '#EC7070']
    colormap = branca.colormap.StepColormap(
        colors, vmin=bins[0], vmax=bins[-1], index=bins, caption='대기환경 (PM10 농도)'
    )

    # GeoJson 객체 추가 (색상 매핑을 위한 목적)
    folium.GeoJson(
        geo_json_data,
        style_function=lambda feature: {
            'fillColor': colormap(input_df.loc[input_df[input_id] == feature['properties']['구'], input_column].values[0]),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7
        }
    ).add_to(m)
    
    # Colormap 범례 추가
    colormap.add_to(m)

    # 각 구의 중앙에 구 이름 표시
    for feature in geo_json_data['features']:
        properties = feature['properties']
        geometry = shape(feature['geometry'])
        centroid = geometry.centroid
        offset = [0, 0]

        # Adjust the vertical offset for Yangcheon-gu
        if properties["구"] == "양천구":
            offset = [0, -0.008]  
        
        if properties["구"] == "금천구":
            offset = [0.006, 0]  

        if properties["구"] == "성북구":
            offset = [0.005, -0.008]  

        if properties["구"] in ["중구", "성동구", "도봉구", "광진구", "중랑구", "은평구"]:
            offset = [0.005, 0]  

        folium.Marker(
            location=[centroid.y + offset[1], centroid.x + offset[0]],
            icon=folium.DivIcon(
                html=f'<div style="font-size: 12px; color: black; font-weight: bold; white-space: nowrap; margin-left: 10px;">{properties["구"]}</div>',
                icon_size=(75, 20)  # Adjust size if necessary
            )
        ).add_to(m)

    return folium_static(m)


################### Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[1]:
    st.markdown('#### PM-10')
    
    query = f'''
        SELECT * 
        FROM "RealtimeCityAir_2024-09-15"
        WHERE "MSRDT" = 202409152100
        '''
    df = execute_query(query)

    make_choropleth(df, 'MSRSTE_NM', selected_air)