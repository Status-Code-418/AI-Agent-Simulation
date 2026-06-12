import json
import re
import urllib.request
from dataclasses import dataclass


# 에이전트가 기억하는 단일 사실과 출처를 담는 데이터 객체입니다.
@dataclass
class Memory:
    fact: str
    source: str


# 대화에 참여하는 에이전트의 상태와 발화를 관리하는 클래스입니다.
class Agent:
    def __init__(self, name: str, age: int, occupation: str, personality: str, memories: list = None):
        self.name = name
        self.age = age
        self.occ = occupation
        self.personality = personality

        self.memories: list[Memory] = memories if memories else []
        self.reflections: dict[str, str] = {}
        self.met_agents: set[str] = set()
        self.schedule: dict[str, str] = {}
        self.plan_text: str = ""

    # 새로운 기억을 에이전트의 기억 목록에 추가합니다.
    def add_memory(self, memory: Memory):
        self.memories.append(memory)

    # 특정 대상에 대한 관계 정보를 갱신합니다.
    def update_relation(self, target: str, relation: str):
        self.reflections[target] = relation

    # 에이전트의 정보, 기억, 대화 규칙을 포함한 시스템 프롬프트를 만듭니다.
    def system_prompt(self, participants: list[str], topic: str | None) -> str:
        prompt = [
            f"당신의 이름은 {self.name}입니다.",
            f"당신의 나이는 {self.age}입니다.",
            f"당신의 직업은 {self.occ}입니다.",
            f"당신의 성격은 {self.personality}",
        ]

        if self.memories:
            prompt.append("당신이 알고 있는 사실:")
            for memory in self.memories:
                prompt.append(f"- [{memory.source}]에 대한 정보: {memory.fact}")

        prompt.append(f"현재 대화에 참여 중인 사람: {', '.join(participants)}")

        first_time_meeting = any(p != self.name and p not in self.met_agents for p in participants)

        if first_time_meeting:
            prompt.append(
                "처음 만나는 사람이 있습니다. 주제를 강제로 꺼내지 말고 자연스럽게 인사와 자기소개로 대화를 시작하세요."
            )
        elif topic:
            prompt.append(f"현재 대화 주제: {topic}")
        else:
            prompt.append("정해진 대화 주제가 없습니다. 기억이나 상황을 바탕으로 자연스럽게 대화 주제를 꺼내세요.")

        # 지시문과 괄호 표현을 금지하는 대화 규칙을 추가합니다.
        prompt.append("이전 대화의 맥락을 이어받아 자연스럽게 한 번만 발언하세요. 상대방의 말에 반응하는 것이 좋습니다.")
        prompt.append("반드시 한국어로만 대화하세요.")
        prompt.append("대답을 시작할 때 화자 이름이나 'Assistant', 'assistant:' 같은 접두어를 붙이지 마세요.")
        prompt.append("중요: 괄호로 둘러싼 행동이나 감정 묘사를 쓰지 말고, 직접 말하는 대사만 출력하세요.")
        return "\n".join(prompt)

    # 이전 대화와 참여자 정보를 바탕으로 Ollama API를 호출해 발화를 생성합니다.
    def speak(self, prev_conversation: list[dict], participants: list[str], topic: str | None):
        sys_prompt = self.system_prompt(participants, topic)

        messages = [{"role": "system", "content": sys_prompt}]

        for conv in prev_conversation:
            role = "assistant" if conv["speaker"] == self.name else "user"
            content = f"{conv['speaker']}의 말: {conv['message']}" if role == "user" else conv["message"]
            messages.append({"role": role, "content": content})

        # 표준 라이브러리만 사용해 로컬 Ollama API를 호출합니다.
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": "llama3.1",
            "messages": messages,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            saying = res_json["message"]["content"].strip()

            saying = re.sub(r"\([^)]*\)", "", saying).strip()
            saying = re.sub(fr"^(?:{self.name}\s*:?\s*|assistant\s*:?\s*)+", "", saying, flags=re.IGNORECASE).strip()

        for participant in participants:
            if participant != self.name:
                self.met_agents.add(participant)

        return saying
