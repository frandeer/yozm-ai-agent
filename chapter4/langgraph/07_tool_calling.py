from typing import Dict, Any, Literal, List
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import random
import time
import math
import json


# ① 워크플로우 단계 정의
class WorkflowStep:
    QUERY_ANALYZER = "QUERY_ANALYZER"
    CALCULATOR = "CALCULATOR"
    WEATHER_API = "WEATHER_API"
    CURRENCY_CONVERTER = "CURRENCY_CONVERTER"
    RESULT_FORMATTER = "RESULT_FORMATTER"


# ② 도구 정의
class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


# ③ 그래프 상태 정의
class ToolCallingState(BaseModel):
    user_query: str = Field(default="", description="사용자 질문")
    detected_intent: str = Field(default="", description="감지된 의도")
    tool_name: str = Field(default="", description="사용할 도구 이름")
    tool_input: Dict[str, Any] = Field(default_factory=dict, description="도구 입력 파라미터")
    tool_output: Dict[str, Any] = Field(default_factory=dict, description="도구 실행 결과")
    final_answer: str = Field(default="", description="최종 답변")
    available_tools: List[ToolDefinition] = Field(default_factory=list, description="사용 가능한 도구들")


# ④ 사용 가능한 도구들 정의
AVAILABLE_TOOLS = [
    ToolDefinition(
        name="calculator",
        description="수학 계산을 수행합니다. 사칙연산, 제곱근, 삼각함수 등을 지원합니다.",
        parameters={
            "expression": "계산할 수식 (예: '2 + 3 * 4', 'sqrt(16)', 'sin(30)')"
        }
    ),
    ToolDefinition(
        name="weather",
        description="특정 도시의 현재 날씨 정보를 조회합니다.",
        parameters={
            "city": "날씨를 확인할 도시명",
            "country": "국가명 (선택사항)"
        }
    ),
    ToolDefinition(
        name="currency_converter",
        description="통화 간 환율을 계산하여 금액을 변환합니다.",
        parameters={
            "amount": "변환할 금액",
            "from_currency": "원본 통화 코드 (예: USD, KRW)",
            "to_currency": "대상 통화 코드 (예: USD, KRW)"
        }
    )
]


# ⑤ 쿼리 분석 노드
def query_analyzer(state: ToolCallingState) -> Dict[str, Any]:
    query = state.user_query.lower()
    
    print(f"[query_analyzer] 🔍 쿼리 분석 중: '{state.user_query}'")
    
    # 의도 감지 패턴
    intent_patterns = {
        "calculator": [
            "계산", "더하기", "빼기", "곱하기", "나누기", "제곱", "루트", "sin", "cos", "tan",
            "+", "-", "*", "/", "=", "수학", "공식"
        ],
        "weather": [
            "날씨", "기온", "온도", "비", "눈", "맑음", "흐림", "습도", "바람", "weather"
        ],
        "currency_converter": [
            "환율", "달러", "원", "엔", "유로", "currency", "usd", "krw", "jpy", "eur", "변환", "환전"
        ]
    }
    
    # 의도 점수 계산
    intent_scores = {}
    for intent, keywords in intent_patterns.items():
        score = sum(1 for keyword in keywords if keyword in query)
        if score > 0:
            intent_scores[intent] = score
    
    # 가장 높은 점수의 의도 선택
    if intent_scores:
        detected_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[detected_intent] / len(intent_patterns[detected_intent])
    else:
        detected_intent = "unknown"
        confidence = 0.0
    
    print(f"[query_analyzer] 🎯 감지된 의도: {detected_intent} (신뢰도: {confidence:.2f})")
    
    # 파라미터 추출
    tool_input = {}
    
    if detected_intent == "calculator":
        # 수식 추출 (간단한 패턴)
        import re
        math_pattern = r'[\d\+\-\*/\(\)\s\.]+'
        matches = re.findall(math_pattern, state.user_query)
        if matches:
            expression = matches[0].strip()
        else:
            expression = state.user_query
        tool_input = {"expression": expression}
    
    elif detected_intent == "weather":
        # 도시명 추출
        cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", 
                 "seoul", "busan", "daegu", "incheon", "tokyo", "osaka", "new york", "london", "paris"]
        city = "서울"  # 기본값
        for c in cities:
            if c in query:
                city = c
                break
        tool_input = {"city": city}
    
    elif detected_intent == "currency_converter":
        # 통화 및 금액 추출 (간단한 패턴)
        amount = 100  # 기본값
        from_currency = "USD"
        to_currency = "KRW"
        
        # 숫자 추출
        import re
        numbers = re.findall(r'\d+', state.user_query)
        if numbers:
            amount = int(numbers[0])
        
        # 통화 코드 추출
        currencies = ["usd", "krw", "jpy", "eur", "cny"]
        found_currencies = [curr.upper() for curr in currencies if curr in query]
        if len(found_currencies) >= 2:
            from_currency = found_currencies[0]
            to_currency = found_currencies[1]
        elif len(found_currencies) == 1:
            if "달러" in query or "usd" in query:
                from_currency = "USD"
                to_currency = "KRW"
            elif "원" in query or "krw" in query:
                from_currency = "KRW"
                to_currency = "USD"
        
        tool_input = {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency
        }
    
    print(f"[query_analyzer] 📋 추출된 파라미터: {tool_input}")
    
    return {
        "detected_intent": detected_intent,
        "tool_name": detected_intent,
        "tool_input": tool_input,
        "available_tools": AVAILABLE_TOOLS
    }


# ⑥ 계산기 도구
def calculator(state: ToolCallingState) -> Dict[str, Any]:
    expression = state.tool_input.get("expression", "")
    
    print(f"[calculator] 🧮 계산 실행: {expression}")
    
    try:
        # 안전한 수학 표현식 평가
        # 기본 수학 함수들 허용
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        allowed_names.update({"abs": abs, "round": round})
        
        # 위험한 함수들 제거
        for dangerous in ["exec", "eval", "open", "import"]:
            allowed_names.pop(dangerous, None)
        
        # 표현식 전처리 (일반적인 함수명 변환)
        expression = expression.replace("sqrt", "math.sqrt")
        expression = expression.replace("sin", "math.sin")
        expression = expression.replace("cos", "math.cos")
        expression = expression.replace("tan", "math.tan")
        expression = expression.replace("log", "math.log")
        
        # 계산 실행
        result = eval(expression, {"__builtins__": {}, "math": math}, allowed_names)
        
        # 결과 포맷팅
        if isinstance(result, float):
            if result.is_integer():
                result = int(result)
            else:
                result = round(result, 6)
        
        tool_output = {
            "status": "success",
            "result": result,
            "expression": expression,
            "type": type(result).__name__
        }
        
        print(f"[calculator] ✅ 계산 완료: {result}")
        
    except Exception as e:
        tool_output = {
            "status": "error",
            "error": str(e),
            "expression": expression
        }
        
        print(f"[calculator] ❌ 계산 실패: {e}")
    
    return {"tool_output": tool_output}


# ⑦ 날씨 API 도구 (시뮬레이션)
def weather_api(state: ToolCallingState) -> Dict[str, Any]:
    city = state.tool_input.get("city", "서울")
    country = state.tool_input.get("country", "")
    
    print(f"[weather_api] 🌤️ 날씨 정보 조회: {city}")
    
    # API 호출 시뮬레이션
    time.sleep(random.uniform(0.5, 1.5))
    
    # 가상의 날씨 데이터
    weather_data = {
        "서울": {"temp": 15, "condition": "맑음", "humidity": 60, "wind": 10},
        "부산": {"temp": 18, "condition": "흐림", "humidity": 70, "wind": 15},
        "seoul": {"temp": 15, "condition": "clear", "humidity": 60, "wind": 10},
        "tokyo": {"temp": 12, "condition": "rainy", "humidity": 80, "wind": 8},
        "new york": {"temp": 5, "condition": "snowy", "humidity": 40, "wind": 20},
        "london": {"temp": 8, "condition": "cloudy", "humidity": 75, "wind": 12}
    }
    
    # 도시별 날씨 조회
    city_key = city.lower()
    if city_key in weather_data:
        data = weather_data[city_key]
        
        tool_output = {
            "status": "success",
            "city": city,
            "temperature": data["temp"],
            "condition": data["condition"],
            "humidity": data["humidity"],
            "wind_speed": data["wind"],
            "unit": "°C"
        }
        
        print(f"[weather_api] ✅ 날씨 조회 완료: {data['temp']}°C, {data['condition']}")
        
    else:
        # 기본 랜덤 날씨
        conditions = ["맑음", "흐림", "비", "눈"]
        tool_output = {
            "status": "success",
            "city": city,
            "temperature": random.randint(-5, 30),
            "condition": random.choice(conditions),
            "humidity": random.randint(40, 90),
            "wind_speed": random.randint(0, 25),
            "unit": "°C"
        }
        
        print(f"[weather_api] ✅ 기본 날씨 제공: {tool_output['temperature']}°C")
    
    return {"tool_output": tool_output}


# ⑧ 환율 변환 도구 (시뮬레이션)
def currency_converter(state: ToolCallingState) -> Dict[str, Any]:
    amount = state.tool_input.get("amount", 100)
    from_currency = state.tool_input.get("from_currency", "USD")
    to_currency = state.tool_input.get("to_currency", "KRW")
    
    print(f"[currency_converter] 💱 환율 변환: {amount} {from_currency} → {to_currency}")
    
    # API 호출 시뮬레이션
    time.sleep(random.uniform(0.3, 1.0))
    
    # 가상의 환율 데이터 (실제로는 API에서 가져옴)
    exchange_rates = {
        ("USD", "KRW"): 1320.50,
        ("KRW", "USD"): 1/1320.50,
        ("USD", "JPY"): 149.80,
        ("JPY", "USD"): 1/149.80,
        ("USD", "EUR"): 0.92,
        ("EUR", "USD"): 1/0.92,
        ("KRW", "JPY"): 0.113,
        ("JPY", "KRW"): 8.85,
        ("EUR", "KRW"): 1435.60,
        ("KRW", "EUR"): 1/1435.60
    }
    
    # 환율 조회
    rate_key = (from_currency, to_currency)
    
    if rate_key in exchange_rates:
        exchange_rate = exchange_rates[rate_key]
        converted_amount = amount * exchange_rate
        
        tool_output = {
            "status": "success",
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": round(exchange_rate, 4),
            "converted_amount": round(converted_amount, 2)
        }
        
        print(f"[currency_converter] ✅ 변환 완료: {converted_amount} {to_currency}")
        
    elif from_currency == to_currency:
        # 같은 통화
        tool_output = {
            "status": "success",
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": 1.0,
            "converted_amount": amount
        }
        
        print(f"[currency_converter] ✅ 동일 통화: {amount} {from_currency}")
        
    else:
        # 지원하지 않는 통화 쌍
        tool_output = {
            "status": "error",
            "error": f"환율 정보를 찾을 수 없습니다: {from_currency} → {to_currency}",
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        
        print(f"[currency_converter] ❌ 지원하지 않는 통화 쌍")
    
    return {"tool_output": tool_output}


# ⑨ 결과 포맷터 노드
def result_formatter(state: ToolCallingState) -> Dict[str, Any]:
    tool_name = state.tool_name
    tool_output = state.tool_output
    
    print(f"[result_formatter] 📝 결과 포맷팅 중...")
    
    if tool_output.get("status") == "error":
        final_answer = f"❌ 오류가 발생했습니다: {tool_output.get('error', '알 수 없는 오류')}"
    
    elif tool_name == "calculator":
        result = tool_output.get("result")
        expression = tool_output.get("expression")
        final_answer = f"🧮 계산 결과: {expression} = {result}"
    
    elif tool_name == "weather":
        city = tool_output.get("city")
        temp = tool_output.get("temperature")
        condition = tool_output.get("condition")
        humidity = tool_output.get("humidity")
        wind = tool_output.get("wind_speed")
        
        final_answer = (
            f"🌤️ {city} 날씨 정보:\n"
            f"   🌡️ 온도: {temp}°C\n"
            f"   ☁️ 상태: {condition}\n"
            f"   💧 습도: {humidity}%\n"
            f"   💨 풍속: {wind}m/s"
        )
    
    elif tool_name == "currency_converter":
        original = tool_output.get("original_amount")
        from_curr = tool_output.get("from_currency")
        to_curr = tool_output.get("to_currency")
        converted = tool_output.get("converted_amount")
        rate = tool_output.get("exchange_rate")
        
        final_answer = (
            f"💱 환율 변환 결과:\n"
            f"   {original} {from_curr} = {converted} {to_curr}\n"
            f"   환율: 1 {from_curr} = {rate} {to_curr}"
        )
    
    else:
        final_answer = "❓ 알 수 없는 도구 결과입니다."
    
    print(f"[result_formatter] ✅ 포맷팅 완료")
    
    return {"final_answer": final_answer}


# ⑩ 라우팅 함수
def route_to_tool(state: ToolCallingState) -> Literal["calculator", "weather", "currency_converter", "formatter"]:
    """감지된 의도에 따라 적절한 도구로 라우팅"""
    tool_name = state.tool_name
    
    if tool_name in ["calculator", "weather", "currency_converter"]:
        return tool_name
    else:
        return "formatter"  # 알 수 없는 의도는 바로 포맷터로


# ⑪ 그래프 생성 (도구 호출 포함)
def create_tool_calling_graph():
    workflow = StateGraph(ToolCallingState)
    
    # 노드 추가
    workflow.add_node(WorkflowStep.QUERY_ANALYZER, query_analyzer)
    workflow.add_node(WorkflowStep.CALCULATOR, calculator)
    workflow.add_node(WorkflowStep.WEATHER_API, weather_api)
    workflow.add_node(WorkflowStep.CURRENCY_CONVERTER, currency_converter)
    workflow.add_node(WorkflowStep.RESULT_FORMATTER, result_formatter)
    
    # 시작점 설정
    workflow.add_edge(START, WorkflowStep.QUERY_ANALYZER)
    
    # 쿼리 분석 후 도구별 라우팅 (핵심 도구 호출!)
    workflow.add_conditional_edges(
        WorkflowStep.QUERY_ANALYZER,
        route_to_tool,
        {
            "calculator": WorkflowStep.CALCULATOR,
            "weather": WorkflowStep.WEATHER_API,
            "currency_converter": WorkflowStep.CURRENCY_CONVERTER,
            "formatter": WorkflowStep.RESULT_FORMATTER  # 의도 불명확한 경우
        }
    )
    
    # 모든 도구에서 결과 포맷터로
    workflow.add_edge(WorkflowStep.CALCULATOR, WorkflowStep.RESULT_FORMATTER)
    workflow.add_edge(WorkflowStep.WEATHER_API, WorkflowStep.RESULT_FORMATTER)
    workflow.add_edge(WorkflowStep.CURRENCY_CONVERTER, WorkflowStep.RESULT_FORMATTER)
    
    # 결과 포맷터에서 종료
    workflow.add_edge(WorkflowStep.RESULT_FORMATTER, END)
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


# ⑫ 테스트 함수
def test_tool_calling():
    print("=== 도구 호출 AI 어시스턴트 테스트 ===\n")
    
    app = create_tool_calling_graph()
    
    # 다양한 테스트 쿼리
    test_queries = [
        "2 + 3 * 4를 계산해줘",
        "서울 날씨 어때?",
        "100달러를 원화로 바꿔줘",
        "sqrt(16) + sin(30)을 계산해줘",
        "부산의 현재 날씨를 알려줘",
        "1000원을 달러로 환전하면 얼마야?",
        "5의 제곱은?",
        "도쿄 날씨는 어떤가요?",
        "50유로를 원화로 변환해줘"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 테스트 {i}: {query} ---")
        
        initial_state = ToolCallingState(user_query=query)
        
        # 그래프 실행 (도구 자동 선택 및 호출)
        final_state = app.invoke(initial_state)
        
        print(f"\n🤖 AI 어시스턴트 답변:")
        print(final_state['final_answer'])
        print("-" * 50)


# ⑬ 도구 기능 시연
def demo_tool_capabilities():
    print("\n=== 도구 기능 시연 ===\n")
    
    app = create_tool_calling_graph()
    
    print("📋 사용 가능한 도구들:")
    for tool in AVAILABLE_TOOLS:
        print(f"   🔧 {tool.name}: {tool.description}")
    
    # 각 도구별 시연
    demos = [
        {
            "category": "🧮 계산기",
            "queries": [
                "3.14 * 2의 제곱을 계산해줘",
                "sin(45) + cos(45)는?",
                "sqrt(144) - 5는 얼마야?"
            ]
        },
        {
            "category": "🌤️ 날씨 조회",
            "queries": [
                "런던 날씨 알려줘",
                "뉴욕의 현재 기온은?",
                "오사카 날씨 어때?"
            ]
        },
        {
            "category": "💱 환율 변환",
            "queries": [
                "500엔을 원화로 바꿔줘",
                "200유로는 달러로 얼마야?",
                "1000달러를 엔화로 환전하면?"
            ]
        }
    ]
    
    for demo in demos:
        print(f"\n{demo['category']} 시연:")
        for query in demo['queries']:
            initial_state = ToolCallingState(user_query=query)
            final_state = app.invoke(initial_state)
            
            print(f"   Q: {query}")
            print(f"   A: {final_state['final_answer'].replace(chr(10), chr(10) + '      ')}")
            print()


def main():
    print("=== LangGraph 도구 호출 예제 ===\n")
    
    # 기본 테스트
    test_tool_calling()
    
    # 도구 기능 시연
    demo_tool_capabilities()
    
    # 그래프 시각화
    print("\n=== 워크플로우 시각화 ===")
    app = create_tool_calling_graph()
    
    # ASCII 그래프 출력
    ascii_graph = app.get_graph().draw_ascii()
    print("\n[ASCII 그래프]")
    print(ascii_graph)
    
    # Mermaid PNG 생성
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./07_tool_calling.png", "wb") as f:
            f.write(mermaid_png)
        print("\n[그래프 이미지] 07_tool_calling.png 파일이 생성되었습니다!")
    except Exception as e:
        print(f"\n[그래프 이미지] 생성 실패: {e}")


if __name__ == "__main__":
    main()
