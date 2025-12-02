#!/usr/bin/env python
"""
API功能测试脚本
"""
import requests
import json
import sys

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api"

def test_api_endpoint(method, url, data=None, headers=None, description=""):
    """测试API端点"""
    try:
        print(f"\n{'='*50}")
        print(f"测试: {description}")
        print(f"请求: {method} {url}")

        if data:
            print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}", headers=headers)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{url}", json=data, headers=headers)
        else:
            print(f"不支持的请求方法: {method}")
            return None

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✓ 成功")
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            print("✗ 失败")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误信息: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print("✗ 连接失败 - 请确保Django服务器正在运行")
        return None
    except Exception as e:
        print(f"✗ 请求异常: {e}")
        return None

def main():
    print("轨道交通站务人员AI智能考核系统 - API测试")
    print("=" * 50)

    # 1. 用户登录
    login_data = {
        "job_number": "ST001",
        "password": "password123"
    }

    login_result = test_api_endpoint(
        "POST", "/auth/login/",
        data=login_data,
        description="用户登录"
    )

    if not login_result:
        print("登录失败，无法继续测试")
        return

    token = login_result.get("token")
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

    print(f"\n登录成功! Token: {token[:20]}...")

    # 2. 获取用户信息
    test_api_endpoint(
        "GET", "/auth/profile/",
        headers=headers,
        description="获取用户信息"
    )

    # 3. 生成智能试卷
    exam_data = {
        "reason": "daily_practice",
        "question_count": 5
    }

    generate_result = test_api_endpoint(
        "POST", "/exam/generate/",
        data=exam_data,
        headers=headers,
        description="生成智能试卷"
    )

    if not generate_result:
        print("试卷生成失败")
        return

    paper_id = generate_result.get("paper_id")

    # 4. 获取试卷列表
    test_api_endpoint(
        "GET", "/exam/",
        headers=headers,
        description="获取试卷列表"
    )

    # 5. 开始考试
    test_api_endpoint(
        "POST", f"/exam/{paper_id}/start/",
        headers=headers,
        description="开始考试"
    )

    # 6. 提交考试（模拟答案）
    # 先获取题目信息来构造答案
    paper_detail = test_api_endpoint(
        "GET", f"/exam/{paper_id}/",
        headers=headers,
        description="获取试卷详情"
    )

    if paper_detail and "exam_records" in paper_detail:
        # 构造测试答案
        answers = {}
        for record in paper_detail["exam_records"]:
            question_id = record["question"]["id"]
            question_type = record["question"]["question_type"]

            if question_type == "single":
                answers[str(question_id)] = "A"  # 模拟选择A
            elif question_type == "multiple":
                answers[str(question_id)] = "A,B"  # 模拟选择A和B
            elif question_type == "true_false":
                answers[str(question_id)] = "True"  # 模拟选择True

        submit_data = {"answers": answers}

        test_api_endpoint(
            "POST", f"/exam/{paper_id}/submit/",
            data=submit_data,
            headers=headers,
            description="提交考试答案"
        )

    # 7. 获取能力雷达图数据
    test_api_endpoint(
        "GET", "/analysis/radar/",
        headers=headers,
        description="获取能力雷达图数据"
    )

    # 8. 获取能力总结
    test_api_endpoint(
        "GET", "/analysis/summary/",
        headers=headers,
        description="获取用户能力总结"
    )

    # 9. 获取学习建议
    test_api_endpoint(
        "GET", "/analysis/recommendations/",
        headers=headers,
        description="获取学习建议"
    )

    # 10. 用户登出
    test_api_endpoint(
        "POST", "/auth/logout/",
        headers=headers,
        description="用户登出"
    )

    print(f"\n{'='*50}")
    print("API测试完成!")
    print("如需重新测试，请确保:")
    print("1. Django服务器正在运行 (python manage.py runserver)")
    print("2. 示例数据已初始化 (python manage.py init_sample_data)")

if __name__ == "__main__":
    main()