"""
🌐 스마트 회의록 자동화 시스템 - 웹 버전
=========================================

Flask 기반 웹 인터페이스로 더욱 실용적!
"""

from flask import Flask, render_template, request, jsonify, session
from project_meeting_assistant import (
    MeetingState, 
    generate_summary,
    extract_action_items,
    generate_final_report,
    create_meeting_assistant_graph
)
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# 세션 데이터 저장
sessions_data = {}


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('meeting_assistant.html')


@app.route('/api/start', methods=['POST'])
def start_meeting():
    """회의록 처리 시작"""
    data = request.json
    transcript = data.get('transcript', '')
    team_members = data.get('team_members', [])
    
    # 세션 ID 생성
    session_id = secrets.token_hex(8)
    
    # 초기 상태 생성
    state = MeetingState(
        meeting_transcript=transcript,
        team_members=team_members
    )
    
    # 요약 생성
    summary_result = generate_summary(state)
    state.summary = summary_result['summary']
    
    # 세션에 저장
    sessions_data[session_id] = state
    
    return jsonify({
        'session_id': session_id,
        'summary': state.summary,
        'step': 'summary_review'
    })


@app.route('/api/approve_summary', methods=['POST'])
def approve_summary_api():
    """요약 승인"""
    data = request.json
    session_id = data.get('session_id')
    approved = data.get('approved', False)
    edited_summary = data.get('edited_summary', '')
    
    state = sessions_data.get(session_id)
    if not state:
        return jsonify({'error': 'Session not found'}), 404
    
    if edited_summary:
        state.summary = edited_summary
    
    if approved:
        # 액션 아이템 추출
        action_result = extract_action_items(state)
        state.action_items = action_result['action_items']
        
        sessions_data[session_id] = state
        
        return jsonify({
            'action_items': state.action_items,
            'step': 'action_review'
        })
    else:
        # 재생성 요청
        summary_result = generate_summary(state)
        state.summary = summary_result['summary']
        sessions_data[session_id] = state
        
        return jsonify({
            'summary': state.summary,
            'step': 'summary_review'
        })


@app.route('/api/approve_actions', methods=['POST'])
def approve_actions_api():
    """액션 아이템 승인"""
    data = request.json
    session_id = data.get('session_id')
    action_items = data.get('action_items', [])
    
    state = sessions_data.get(session_id)
    if not state:
        return jsonify({'error': 'Session not found'}), 404
    
    state.action_items = action_items
    
    # 최종 보고서 생성
    report_result = generate_final_report(state)
    state.final_report = report_result['final_report']
    
    sessions_data[session_id] = state
    
    return jsonify({
        'final_report': state.final_report,
        'step': 'final_review'
    })


@app.route('/api/send_report', methods=['POST'])
def send_report_api():
    """보고서 전송"""
    data = request.json
    session_id = data.get('session_id')
    
    state = sessions_data.get(session_id)
    if not state:
        return jsonify({'error': 'Session not found'}), 404
    
    # 실제로는 이메일 전송 등을 수행
    print(f"📧 보고서 전송:")
    print(state.final_report)
    
    return jsonify({
        'success': True,
        'message': '회의록이 성공적으로 전송되었습니다!'
    })


if __name__ == '__main__':
    # templates 디렉토리가 없으면 생성
    os.makedirs('templates', exist_ok=True)
    
    print("""
╔════════════════════════════════════════════════════════╗
║     🌐 스마트 회의록 자동화 시스템 - 웹 버전         ║
╚════════════════════════════════════════════════════════╝

🚀 서버 시작...
📱 브라우저에서 http://localhost:5000 를 여세요!
""")
    
    app.run(debug=True, port=5000)


