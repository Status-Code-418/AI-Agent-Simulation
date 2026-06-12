from script.simulation import Simulation


# 시뮬레이션 실행 후 대학원생 관점 리포트를 생성합니다.
def main():
    print("Ollama llama3.1 기반 다중 에이전트 대화 시뮬레이션을 실행합니다.\n")
    sim = Simulation()
    sim.run_simulation()
    sim.generate_report("대학원생")


if __name__ == "__main__":
    main()
