from openai import OpenAI

client = OpenAI()


def chatbot_response(user_message: str, response_id=None):
    result = client.responses.create(
        model="gpt-4.1-mini", input=user_message, previous_response_id=response_id
    )
    return result


if __name__ == "__main__":
    # 여기서 사용자 메시지를 입력받고 응답을 출력합니다.
    response_id = None
    while True:
        user_message = input("메시지: ")
        if user_message.lower() == "exit":
            print("대화를 종료 합니다.")
            break

        result = chatbot_response(user_message, response_id)
        response_id = result.id
        print(result.output_text)

# 첫번째 예제에는 내 이름을 모른다.
# 두번째 예제에는 내 이름을 알고 있다. response_id를 사용
# Response objects are saved for 30 days by default
# Even when using previous_response_id, all previous input tokens for responses in the chain are billed as input tokens in the API.

# 세번째 예제에서는 어린왕자 페르소나추가
# 네번째 예제에서는 웹화면 추가
