from script.agent import Agent

AGENT = {
    "교수님": Agent(
        name="교수님",
        age=55,
        occupation="대학 교수",
        personality="연구과제를 맡길 대학원생을 찾는 엄격하고 단호한 지도 교수입니다."
    ),
    "대학원생": Agent(
        name="대학원생",
        age=29,
        occupation="대학원생",
        personality="부담스러운 과제를 피하려고 조심스럽게 도망치려는 성실하지만 스트레스를 받는 학생입니다."
    ),
}

ROUNDS = [
    {
        "agents": ["교수님", "대학원생"],
        "topic": "새로운 연구과제 배정과 대학원생의 회피 시도",
        "turns": 2
    },
    {
        "agents": ["교수님", "대학원생"],
        "topic": "연구 진행 상황 확인과 대학원생의 간절한 요청",
        "turns": 2
    },
    {
        "agents": ["교수님", "대학원생"],
        "topic": "최종 제출 기한 압박과 설득의 대화",
        "turns": 2
    }
] # 각 라운드마다 참여자와 주제, 턴 수를 정의