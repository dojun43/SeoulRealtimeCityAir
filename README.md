# 서울시 실시간 대기현황 
## Overview 
이 프로젝트는 서울시의 실시간 대기현황 데이터를 매시간 수집하여 정형화된 형식으로 저장하고, 이를 분석 및 시각화를 위해 사용할 수 있도록 설계된 데이터 파이프라인입니다. 

서울시 열린데이터 광장 API를 통해 대기현황 데이터를 수집하며, Apache Airflow를 사용해 스케줄링을 자동화했습니다. 

Terraform을 이용해 GCE 인프라를 구성하고, Docker 환경에서 Apache Airflow를 배포하여 데이터 파이프라인을 구성했습니다.

## Getting Started
### Prerequisites
- Python 3.12.10
- Google Cloud Platform (GCP) 계정
- Terraform v1.9.5

### Setup
이 프로젝트는 Google Cloud Platform과 Docker 환경을 기반으로 작동합니다. 아래 단계에 따라 환경을 설정하고, 데이터 파이프라인을 실행할 수 있습니다. 각 단계에서 필요한 의존성 설치 및 구성 방법을 안내합니다.

#### 1. Google Cloud 인프라 구성 (Terraform 사용)
- gcp service account json파일을 git repository home의 private 경로에 생성합니다.
```
SeoulRealtimeCityAir\private\gcp_account.json
``` 
 
- terraform/variables.tf에서 credentials의 default에 gcp_account.json의 경로를 지정하고, project의 default에 GCP 프로젝트 이름 지정합니다.
```
variable "credentials" {
  description = "GCP에 액세스하기 위한 json 파일"
  default = "[gcp_account.json 경로 지정]"
}

variable "project" {
  description = "GCP 프로젝트 이름"
  default = "[GCP 프로젝트 이름 지정]" 
}
```
 
- terraform을 초기화하고, 적용하여 GCE 인스턴스를 생성합니다.
```
terraform init
terraform apply
```

#### 2. Docker 및 Airflow 환경 구성
- GCE 인스턴스에 접속한 후, .env 파일에 airflow uid를 입력합니다.

```
cd SeoulRealtimeCityAir

echo -e "AIRFLOW_UID=$(id -u)" > .env
```

- .env 파일에 Postgres와 Postgres custom 컨테이너에서 사용할 유저명과 패스워드를 지정합니다. 
```
vi .env

POSTGRES_CUSTOM_USER=[DB 유저명 설정]
POSTGRES_CUSTOM_PASSWORD=[패스워드 설정]

POSTGRES_USER=[DB 유저명 설정]
POSTGRES_PASSWORD=[패스워드 설정]
```

- Docker Compose를 사용하여 Airflow를 설정하고 초기화하고, 필요한 컨테이너들을 백그라운드에서 실행합니다.
```
sudo docker compose up airflow-init
sudo docker compose up -d
```

#### 3. Airflow Connection 및 Variables 설정
- Airflow 웹 UI (http://<GCE_INSTANCE_IP>:8080)에 접속하여 Airflow Variables 및 Airflow Connection에 필요한 연결 정보를 추가합니다.
- 참고: https://doodo0126.tistory.com/35 


## Architecture
### Data Sources 
- 서울시 열린데이터 광장: https://data.seoul.go.kr/dataList/OA-2219/S/1/datasetView.do
### Extract 
- 서울시 공공데이터 API를 통해 1시간마다 현재 시간의 데이터가 정상적으로 업데이트되었는지 확인하고, 서울시 대기현황 데이터를 추출합니다.
- 정상적으로 업로드되지 않았다면 10분마다 업데이트 상태를 확인하고, 다음 task로 넘어가지 않도록 대기합니다.
### Transform 
- 추출한 데이터를 날짜 별로 테이블을 생성합니다.
### Load 
- 생성된 데이터를 Postgres에 저장합니다.
  

