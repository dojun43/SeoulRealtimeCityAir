import json
import folium
import branca
from shapely.geometry import shape
from streamlit_folium import folium_static
import pandas as pd
import altair as alt


def make_map(input_df, input_id, input_column):
    # GeoJSON 파일 읽기
    geo_data = 'seoul_geo_gu.json'
    with open(geo_data, encoding='utf-8') as f:
        geo_json_data = json.load(f)
    
    # 중심 좌표 설정
    center = [37.567, 126.986]
    m = folium.Map(location=center, zoom_start=10.5)

    # Custom colormap 설정
    if input_column == 'PM25':
        bins = [0, 16, 36, 76, 300]
        colors = ['#5C8CDD', '#65B24B', '#E2D058', '#EC7070']

    if input_column == 'PM10':
        bins = [0, 31, 81, 151, 300]
        colors = ['#5C8CDD', '#65B24B', '#E2D058', '#EC7070']

    if input_column == 'O3':
        bins = [0, 0.031, 0.091, 0.151, 0.3]
        colors = ['#5C8CDD', '#65B24B', '#E2D058', '#EC7070']

    colormap = branca.colormap.StepColormap(
        colors, vmin=bins[0], vmax=bins[-1], index=bins, caption='범례'
    )

    # GeoJson 객체 추가 
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
                icon_size=(75, 20)  
            )
        ).add_to(m)

    return folium_static(m)

def make_donut(title, input_value, input_ratio, input_status):
    # 색상 설정
    if input_status == '좋음':
        chart_color = ['#29b5e8', '#155F7A']  # blue
    elif input_status == '보통':
        chart_color = ['#27AE60', '#12783D']  # green
    elif input_status == '나쁨':
        chart_color = ['#F39C12', '#875A12']  # orange
    elif input_status == '매우나쁨':
        chart_color = ['#E74C3C', '#781F16']  # red
    
    # 데이터프레임 생성
    source = pd.DataFrame({
        "Topic": ['', input_status],
        "% value": [100 - input_ratio, input_ratio]
    })
    
    source_bg = pd.DataFrame({
        "Topic": ['', input_status],
        "% value": [100, 0]
    })
    
    # 도넛 차트 생성
    plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
        theta=alt.Theta("% value:Q", sort="descending"),
        color=alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_status, ''],
                            range=chart_color),
                        legend=None)
    ).properties(width=130, height=130)
    
    # 차트 안에 텍스트 추가
    text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=24, fontWeight=700, fontStyle="italic").encode(
    text=alt.value(f'{input_value}')
    )
            
    plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
        theta="% value",
        color=alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_status, ''],
                            range=chart_color),
                        legend=None)
    ).properties(width=130, height=130)
    
    # 차트 위의 텍스트
    top_title = alt.Chart(pd.DataFrame({'text': [title]})).mark_text(
        align='center',
        fontSize=18,
        fontWeight='bold'
    ).encode(
        text='text:N'
    ).properties(
        width=130,
        height=20
    )

    # 차트 아래의 텍스트
    bottom_title = alt.Chart(pd.DataFrame({'text': [input_status]})).mark_text(
    align='center',
    fontSize=16,
    fontWeight='bold'
    ).encode(
        text='text:N'
    ).properties(
        width=130,
        height=20
    )
    
    return alt.vconcat(top_title, plot_bg + plot + text, bottom_title)