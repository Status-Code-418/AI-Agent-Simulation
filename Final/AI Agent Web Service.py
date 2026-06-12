import json
import urllib.request

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

app = Flask(__name__, template_folder="htdocs")


def build_prompt(mode: str, text: str) -> str:
    if mode == "study":
        return (
            "다음 학습 내용을 바탕으로 학생에게 도움을 주는 AI 학습 도우미로 답하세요.\n"
            "1) 핵심 개념을 간단히 설명\n"
            "2) 이해를 돕는 예시 1개\n"
            "3) 짧은 퀴즈 2개\n"
            f"학습 내용:\n{text}"
        )
    if mode == "meeting":
        return (
            "다음은 회의록입니다. 회의 요약, 핵심 포인트, 그리고 실행할 액션 아이템을 JSON 형식으로만 출력하세요.\n"
            '형식: {"summary":"...", "key_points": ["..."], "action_items": ["..."]}\n'
            f"회의록:\n{text}"
        )
    if mode == "travel":
        return (
            "사용자의 취향을 반영해 여행지나 맛집을 추천하세요.\n"
            "추천 이유, 예상 비용, 방문 포인트를 포함해 3곳 추천하고, 각 항목은 한국어로 간결하게 작성하세요.\n"
            f"취향/요청:\n{text}"
        )
    if mode == "resume":
        return (
            "다음 이력서/자소서 문장을 보고 개선안을 제안하세요.\n"
            "1) 문장 개선\n"
            "2) 더 강한 표현으로 바꾼 버전\n"
            "3) 지원 포지션에 맞는 조언\n"
            f"내용:\n{text}"
        )
    return text


def stream_ollama(prompt_text: str, model: str = "llama3.1"):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "당신은 한국어 AI 도우미입니다. 결과는 자연스럽고 실용적으로 작성하세요."},
            {"role": "user", "content": prompt_text},
        ],
        "stream": True,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            total_received = 0
            full_text = ""
            yield f"event: progress\ndata: {json.dumps({'progress': 10, 'message': '모델 연결 중입니다.'})}\n\n"

            for raw_line in response:
                line = raw_line.decode("utf-8", "ignore").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                chunk = obj.get("message", {}).get("content", "") or ""
                if chunk:
                    full_text += chunk
                    total_received += len(chunk.encode("utf-8"))
                    progress = min(99, 10 + int(total_received / 8))
                    yield f"event: progress\ndata: {json.dumps({'progress': progress, 'message': '응답 생성 중입니다.'})}\n\n"
                    yield f"event: delta\ndata: {json.dumps({'text': chunk})}\n\n"

                if obj.get("done") is True:
                    yield f"event: progress\ndata: {json.dumps({'progress': 100, 'message': '응답 생성 완료'})}\n\n"
                    yield f"event: done\ndata: {json.dumps({'text': full_text})}\n\n"
                    return
    except Exception as exc:
        msg = str(exc)
        if "timed out" in msg.lower():
            msg = "Ollama 응답이 너무 늦습니다. Ollama 서버가 실행 중인지 확인해 주세요."
        yield f"event: error\ndata: {json.dumps({'error': msg})}\n\n"


@app.get("/")
@app.get("/index.html")
def index():
    return render_template("index.html")


@app.post("/api/assistant")
def assistant():
    data = request.json or {}
    mode = data.get("mode", "study")
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "입력 내용을 작성해 주세요."}), 400

    prompt = build_prompt(mode, text)
    return jsonify({"mode": mode, "result": {"summary": prompt}})


@app.get("/api/assistant_stream")
def assistant_stream():
    mode = request.args.get("mode", "study")
    text = (request.args.get("text") or "").strip()

    if not text:
        return Response("event: error\ndata: {\"error\":\"입력 내용을 작성해 주세요.\"}\n\n", mimetype="text/event-stream")

    prompt = build_prompt(mode, text)

    return Response(
        stream_with_context(stream_ollama(prompt)),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
