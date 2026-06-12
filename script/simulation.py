import json
import re
import urllib.request

from script.agent import Memory
from script.preset import AGENT, ROUNDS


# Ollama API 호출을 공통으로 처리하는 함수입니다.
def call_ollama_api(prompt_text: str) -> str:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.1",
        "messages": [{"role": "user", "content": prompt_text}],
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            return res_json["message"]["content"].strip()
    except Exception as e:
        print(f"[경고] Ollama API 호출 실패: {e}")
        return ""


# 전체 대화 흐름, 일정, 기억 반영, 리포트 저장을 조율하는 클래스입니다.
class Simulation:
    def __init__(self):
        self.agents = AGENT
        self.rounds = ROUNDS
        self.history = []
        self.output_lines = []
        self.time_slots = ["08:00-12:00", "12:00-17:00", "17:00-22:00"]
        self.locations = ["집", "학교", "카페", "연구실"]
        self.days = 2

    # 시뮬레이션 실행 순서를 정의합니다.
    def run_simulation(self):
        self.plan_schedules()
        self.run_preset_rounds()
        self.run_timed_conversations()

    # 각 에이전트의 하루 일정을 생성하고 기본 일정으로 보정합니다.
    def plan_schedules(self):
        for agent in self.agents.values():
            plan_prompt = (
                f"당신은 {agent.name}입니다. 08:00부터 22:00까지 하루를 세 개의 시간대(오전, 오후, 저녁)로 나누어 "
                f"장소 계획을 세우세요. 가능한 장소는 {', '.join(self.locations)}입니다. "
                "각 줄을 '08:00-12:00: 장소', '12:00-17:00: 장소', '17:00-22:00: 장소' 형식으로 작성하세요."
            )
            plan_text = call_ollama_api(plan_prompt)
            agent.plan_text = plan_text
            agent.schedule = self.parse_plan_text(plan_text)
            if len(agent.schedule) != len(self.time_slots):
                agent.schedule = self.default_schedule(agent.name)
                agent.plan_text = "(기본 일정 사용)"

            self.output_lines.append(f"[PLAN] {agent.name}: {agent.schedule}")

    # LLM 응답에서 시간대별 장소 정보를 추출합니다.
    def parse_plan_text(self, text: str) -> dict:
        schedule = {}
        for match in re.finditer(r"(\d{2}:\d{2}-\d{2}:\d{2})\s*[:\-]?\s*([^\n]+)", text):
            time_range = match.group(1).strip()
            place = match.group(2).strip()
            schedule[time_range] = place
        return schedule

    # 일정 생성에 실패했을 때 사용할 기본 일정을 반환합니다.
    def default_schedule(self, agent_name: str) -> dict:
        if agent_name == "교수님":
            return {
                "08:00-12:00": "학교",
                "12:00-17:00": "연구실",
                "17:00-22:00": "카페",
            }
        return {
            "08:00-12:00": "연구실",
            "12:00-17:00": "카페",
            "17:00-22:00": "집",
        }

    # 사전에 정의된 주제별 대화를 실행합니다.
    def run_preset_rounds(self):
        for r_idx, round_data in enumerate(self.rounds):
            participants = round_data["agents"]
            topic = round_data.get("topic")
            turns = round_data.get("turns", 1)

            round_info = f"\n--- Round {r_idx + 1} ---\n참여자: {', '.join(participants)}"
            if topic:
                round_info += f"\n주제: {topic}"

            print(round_info)
            self.output_lines.append(round_info)

            conversation_history = []
            for _ in range(turns):
                for participant_name in participants:
                    agent = self.agents[participant_name]
                    saying = agent.speak(conversation_history, participants, topic)
                    print(f"{participant_name}: {saying}")
                    self.output_lines.append(f"{participant_name}: {saying}")
                    conversation_history.append({"speaker": participant_name, "message": saying})
                    self.history.append({"speaker": participant_name, "message": saying})

            self.extract_and_reflect(conversation_history, participants)

    # 같은 시간과 장소에 있는 에이전트끼리 추가 대화를 실행합니다.
    def run_timed_conversations(self):
        for day in range(1, self.days + 1):
            day_info = f"\n=== Day {day} 시뮬레이션 ==="
            print(day_info)
            self.output_lines.append(day_info)

            for time_range in self.time_slots:
                location_groups = {}
                for name, agent in self.agents.items():
                    place = agent.schedule.get(time_range, "장소 없음")
                    location_groups.setdefault(place, []).append(name)

                for place, participants in location_groups.items():
                    if len(participants) < 2:
                        continue

                    round_info = f"\n--- Day {day} {time_range} ({place}) ---\n참여자: {', '.join(participants)}"
                    print(round_info)
                    self.output_lines.append(round_info)

                    conversation_history = []
                    topic = f"{place}에서 나누는 일상과 연구 계획 이야기"
                    for participant_name in participants:
                        agent = self.agents[participant_name]
                        saying = agent.speak(conversation_history, participants, topic)
                        print(f"{participant_name}: {saying}")
                        self.output_lines.append(f"{participant_name}: {saying}")
                        conversation_history.append({"speaker": participant_name, "message": saying})
                        self.history.append({"speaker": participant_name, "message": saying})

                    self.extract_and_reflect(conversation_history, participants)

    # 대화 기록에서 사실과 관계 인상을 추출해 에이전트 상태에 반영합니다.
    def extract_and_reflect(self, history: list[dict], participants: list[str]):
        if not history:
            return

        history_text = "\n".join([f"{conv['speaker']}: {conv['message']}" for conv in history])

        for target_name in participants:
            fact_prompt = (
                f"다음 대화를 읽고 참여자 '{target_name}'에 대해 새롭게 알게 된 구체적인 사실 1가지만 요약하세요.\n"
                f"대화:\n{history_text}\n사실 내용만 한국어로 작성하세요."
            )
            extracted_fact = call_ollama_api(fact_prompt)
            if not extracted_fact:
                continue

            for observer_name in participants:
                if observer_name != target_name:
                    self.agents[observer_name].add_memory(Memory(fact=extracted_fact, source=target_name))
                    self.output_lines.append(f"  -> [Fact 저장] {observer_name}의 기억 <- {target_name}: {extracted_fact}")

        for observer_name in participants:
            for target_name in participants:
                if observer_name == target_name:
                    continue

                reflect_prompt = (
                    f"다음 대화를 읽고 '{observer_name}'이 느낀 '{target_name}'에 대한 관계나 인상을 1문장으로 요약하세요.\n"
                    f"대화:\n{history_text}\n관계 내용만 한국어로 작성하세요."
                )
                reflection = call_ollama_api(reflect_prompt)
                if reflection:
                    self.agents[observer_name].update_relation(target_name, reflection)
                    self.output_lines.append(f"  -> [Reflection 갱신] {observer_name}이 생각하는 {target_name}: {reflection}")

    # 특정 에이전트 관점의 기억과 관계 정보를 리포트로 생성합니다.
    def generate_report(self, agent_name: str):
        if agent_name not in self.agents:
            print(f"{agent_name} 에이전트를 찾을 수 없습니다.")
            return

        agent = self.agents[agent_name]
        report_lines = []
        report_lines.append(f"\n{'=' * 40}")
        report_lines.append(f" {agent_name}의 관점 리포트")
        report_lines.append(f"{'=' * 40}")

        other_agents = [name for name in self.agents.keys() if name != agent.name]
        memory_by_source = {}
        for memory in agent.memories:
            memory_by_source.setdefault(memory.source, []).append(memory.fact)

        for other in other_agents:
            report_lines.append(f"\n[{other}에 대하여]")
            report_lines.append("  [알고 있는 사실 (Fact)]")
            if other in memory_by_source:
                for fact in memory_by_source[other]:
                    report_lines.append(f"   - {fact}")
            else:
                report_lines.append("   - 알려진 사실 없음")

            report_lines.append("  [관계 및 인상 (Reflection)]")
            relation = agent.reflections.get(other, "아직 상호작용이 없거나 관계가 형성되지 않았습니다.")
            report_lines.append(f"   - {relation}")

        report_text = "\n".join(report_lines)
        print(report_text)
        self.output_lines.append(report_text)
        self.save_to_file()

    # 시뮬레이션 출력 내용을 output.txt 파일로 저장합니다.
    def save_to_file(self):
        try:
            with open("output.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(self.output_lines))
            print(f"\n{'=' * 40}")
            print("[완료] 리포트 출력이 끝났습니다. 전체 기록은 'output.txt' 파일에 저장되었습니다.")
            print(f"{'=' * 40}")
        except Exception as e:
            print(f"\n[오류] 파일 저장 중 에러가 발생했습니다: {e}")
