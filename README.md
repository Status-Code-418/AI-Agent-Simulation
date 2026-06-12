# LLM Agent Conversation Simulation

로컬 Ollama 모델을 사용해 여러 에이전트가 대화하고, 대화에서 얻은 사실과 관계 인상을 바탕으로 리포트를 남기는 Python 기반 다중 에이전트 시뮬레이션 프로그램입니다.

## 주요 기능

- `script/preset.py`에 정의된 에이전트와 대화 라운드를 불러와 시뮬레이션을 실행합니다.
- Ollama의 `llama3.1` 모델을 사용해 에이전트의 발화를 생성합니다.
- 각 에이전트는 이름, 나이, 직업, 성격, 기억, 관계 인상을 상태로 가집니다.
- 사전 정의된 주제에 따라 교수님과 대학원생의 대화를 진행합니다.
- 에이전트별 하루 장소 계획을 생성하고, 같은 시간대와 장소에 있는 에이전트끼리 추가 대화를 진행합니다.
- 대화 내용에서 다음 정보를 추출해 에이전트 상태에 반영합니다.
  - `Fact`: 상대에 대해 새롭게 알게 된 사실
  - `Reflection`: 상대에 대한 관계나 인상
- 특정 에이전트 관점의 리포트를 생성합니다.
- 전체 실행 결과는 `output.txt`에 저장됩니다.

## 프로젝트 구조

```text
.
├── main.py
├── README.md
├── output.txt
└── script/
    ├── agent.py
    ├── all.py
    ├── preset.py
    └── simulation.py
```

## 실행 환경

- OS: Windows 11
- Python: 3.10 이상
- Ollama: llama3.1

## Ollama 설치 및 확인

Ollama 모델을 설치하거나 실행합니다.

```powershell
ollama run llama3.1
```

설치된 모델 목록을 확인합니다.

```powershell
ollama list
```

현재 기본 모델명은 코드에서 `llama3.1`로 설정되어 있습니다.

본 프로젝트는 Python 표준 라이브러리만 사용하므로 별도 패키지 설치가 필요하지 않습니다.

## 실행 방법

개발 환경에서 직접 실행합니다.

```powershell
python main.py
```

실행하면 시뮬레이션이 진행되고, 마지막에 `대학원생` 관점의 리포트가 생성됩니다.

## 빌드 방법

단일 실행 파일이 필요하면 PyInstaller를 설치합니다.

```powershell
python -m pip install pyinstaller
```

아래 명령어로 실행 파일을 생성할 수 있습니다.

```powershell
py -3.13 -m PyInstaller --onefile --add-data "script;script" ./main.py
```

빌드가 완료되면 `dist/main.exe` 파일 하나만 배포하면 됩니다. 
**단, 실행하는 환경에 반드시 Ollama가 설치되어 있어야 합니다.**

```powershell
.\dist\main.exe
```

## 동작 흐름

1. `main.py`가 `Simulation` 객체를 생성합니다.
2. `Simulation`이 `script/preset.py`의 `AGENT`와 `ROUNDS` 설정을 불러옵니다.
3. 각 에이전트의 하루 장소 계획을 Ollama로 생성합니다.
4. 일정 생성 결과가 올바르지 않으면 기본 일정으로 대체합니다.
5. `ROUNDS`에 정의된 주제별 대화를 먼저 실행합니다.
6. 같은 시간대와 장소에 있는 에이전트끼리 추가 대화를 실행합니다.
7. 대화 기록에서 사실과 관계 인상을 추출해 각 에이전트의 기억과 관계 상태를 갱신합니다.
8. `generate_report("대학원생")`이 대학원생 관점의 리포트를 출력하고 저장합니다.

## 주요 파일

- `main.py`: 프로그램 실행 진입점
- `script/agent.py`: `Agent`와 `Memory` 정의, 시스템 프롬프트 생성, Ollama 발화 호출
- `script/preset.py`: 기본 에이전트 정보와 사전 대화 라운드 설정
- `script/simulation.py`: 일정 생성, 대화 실행, 기억 반영, 리포트 저장 로직
- `script/all.py`: 외부에서 가져올 주요 객체 목록

## 설정 변경

기본 에이전트와 대화 주제는 `script/preset.py`에서 수정합니다.

- `AGENT`: 에이전트 이름, 나이, 직업, 성격 설정
- `ROUNDS`: 참여자, 대화 주제, 턴 수 설정

시간대, 장소 목록, 시뮬레이션 일수는 `script/simulation.py`의 `Simulation.__init__`에서 수정합니다.

## 결과 파일

- 전체 대화 기록 및 리포트: `output.txt`
- 빌드 실행 파일: `dist/main.exe`
