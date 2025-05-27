from langchain_openai import OpenAIEmbeddings
import numpy as np


def understand_embeddings():
    """임베딩이 무엇인지 시각적으로 이해하기"""
    
    # 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings()
    
    # 더 다양한 주제의 문장들로 구성
    sentences = [
        # 반려동물 관련 문장들 (서로 유사)
        "나는 강아지를 정말 좋아해요",
        "개는 충성스러운 반려동물입니다",
        "고양이도 사랑스러운 동물이에요",
        
        # 음식 관련 문장들 (서로 유사)
        "피자는 이탈리아 음식입니다",
        "파스타도 이탈리아 요리예요",
        
        # 완전히 다른 주제들
        "프로그래밍은 논리적 사고가 필요합니다",
        "양자역학은 물리학의 한 분야입니다",
        "주식 투자는 위험할 수 있습니다"
    ]
    
    # 각 문장을 벡터로 변환
    vectors = []
    for sentence in sentences:
        vector = embeddings.embed_query(sentence)
        vectors.append(vector)
    
    # 벡터 간 유사도 계산 (코사인 유사도)
    def cosine_similarity(vec1, vec2):
        """두 벡터 간의 코사인 유사도를 계산합니다"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # 코사인 유사도 = (A·B) / (||A|| * ||B||)
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        
        return dot_product / (norm_a * norm_b)
    
    # 모든 문장 쌍의 유사도를 계산하여 히트맵 스타일로 표시
    print("=== 임베딩 벡터 정보 ===")
    print(f"벡터 차원: {len(vectors[0])}")
    print(f"첫 번째 벡터의 일부: {vectors[0][:3]}...")
    print()
    
    print("=== 문장 간 유사도 매트릭스 ===")
    print("(값이 1에 가까울수록 유사함)")
    print()
    
    # 유사도 매트릭스 생성
    n = len(sentences)
    similarity_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            similarity_matrix[i][j] = cosine_similarity(vectors[i], vectors[j])
    
    # 매트릭스를 보기 좋게 출력
    print("     ", end="")
    for i in range(n):
        print(f"  [{i}] ", end="")
    print()
    
    for i in range(n):
        print(f"[{i}]  ", end="")
        for j in range(n):
            sim = similarity_matrix[i][j]
            # 자기 자신과의 유사도는 항상 1.0
            if i == j:
                print(" 1.00 ", end="")
            else:
                print(f"{sim:5.3f} ", end="")
        print(f"  {sentences[i][:20]}")
    
    print("\n=== 유사도 분석 ===")
    print("주목할 점:")
    print("1. 같은 주제의 문장들끼리 높은 유사도를 보입니다")
    print("   - 반려동물 문장들 (0-2번): 서로 0.85 이상")
    print("   - 음식 문장들 (3-4번): 서로 0.9 이상")
    print("2. 다른 주제의 문장들은 상대적으로 낮은 유사도를 보입니다")
    print("   - 하지만 여전히 0.7 이상인 경우가 많습니다!")
    
    # 가장 유사한 문장 쌍과 가장 다른 문장 쌍 찾기
    print("\n=== 극단적인 예시 ===")
    
    # 자기 자신을 제외한 가장 높은 유사도
    max_sim = 0
    max_pair = (0, 0)
    min_sim = 1
    min_pair = (0, 0)
    
    for i in range(n):
        for j in range(i+1, n):  # 대각선 위쪽만 확인
            sim = similarity_matrix[i][j]
            if sim > max_sim:
                max_sim = sim
                max_pair = (i, j)
            if sim < min_sim:
                min_sim = sim
                min_pair = (i, j)
    
    print(f"\n가장 유사한 문장 쌍 (유사도: {max_sim:.4f}):")
    print(f"  '{sentences[max_pair[0]]}'")
    print(f"  '{sentences[max_pair[1]]}'")
    
    print(f"\n가장 다른 문장 쌍 (유사도: {min_sim:.4f}):")
    print(f"  '{sentences[min_pair[0]]}'")
    print(f"  '{sentences[min_pair[1]]}'")
    
    # 실제 검색에서의 임계값 가이드
    print("\n=== 실전 임계값 가이드 ===")
    print("OpenAI 임베딩에서의 경험적 임계값:")
    print("- 0.9 이상: 거의 같은 의미")
    print("- 0.85-0.9: 매우 관련성 높음")
    print("- 0.8-0.85: 관련 있음")
    print("- 0.75-0.8: 약간 관련 있음")
    print("- 0.75 미만: 관련성 낮음")
    print("\n💡 팁: 실제 사용 시에는 데이터에 맞게 임계값을 조정하세요!")

understand_embeddings()