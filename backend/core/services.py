import random
import json
import requests
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Question, ExamPaper, ExamRecord, ExamConfig, Tag
from .exam_builder import compose_exam, ComposeError
from .option_shuffle import make_option_order, is_choice_correct
from analysis.models import CapabilityProfile

User = get_user_model()


class ExamGenerationService:
    """组卷服务：按管理员设定的规则抽题，普通员工先按岗位级别筛选候选题。"""

    def generate_exam(self, user_id, reason='daily_practice'):
        """
        为用户生成一份试卷。

        Raises:
            ComposeError: 管理员还没设置组卷规则、员工没有岗位级别、或没有可抽的题
        """
        user = User.objects.get(id=user_id)
        config = ExamConfig.load()
        if config is None or not config.bank_subjects:
            raise ComposeError('管理员还没有设置组卷规则，请联系管理员')

        questions, notes = compose_exam(config, user)
        for note in notes:
            print(f'[组卷提示] 用户 {user.job_number}: {note}')

        with transaction.atomic():
            exam_paper = ExamPaper.objects.create(
                user=user,
                generation_reason=reason,
                status=ExamPaper.Status.NOT_STARTED,
                title=f"{user.job_number}的考核试卷",
                total_score=100.0,  # 固定100分，按实际题数平均分配
            )
            for question in questions:
                ExamRecord.objects.create(
                    paper=exam_paper,
                    question=question,
                    score_gained=0.0,
                    option_order=make_option_order(question),
                )
        return exam_paper


class ExamScoringService:
    """考试评分服务"""

    def __init__(self):
        self.settings = settings.ASSESSMENT_SETTINGS
        self.ai_settings = getattr(settings, 'AI_GRADING_SETTINGS', {})

    def submit_exam(self, paper_id, answers):
        """
        提交试卷并自动评分

        Args:
            paper_id: 试卷ID
            answers: 用户答案字典 {question_id: user_answer}

        Returns:
            dict: 评分结果
        """
        paper = ExamPaper.objects.get(id=paper_id)

        with transaction.atomic():
            # 更新试卷状态
            paper.status = ExamPaper.Status.COMPLETED
            paper.completed_at = timezone.now()

            total_score = 0
            tag_scores = {}  # 记录各标签的得分情况

            # 批量更新答题记录
            records = paper.exam_records.select_related('question').prefetch_related('question__tags')

            for record in records:
                question_id = record.question.id
                user_answer = answers.get(str(question_id), '')

                # 更新用户答案
                record.user_answer = user_answer

                # 判断对错并计分
                result = self._check_answer(record.question, user_answer, record.option_order)

                if record.question.question_type == Question.QuestionType.SUBJECTIVE:
                    # 主观题：result是AI评分的分数(0-100)
                    ai_score = result
                    print(f"[AI评分] 主观题ID:{record.question.id}, AI评分: {ai_score}")
                    # 将分数按比例转换为题目得分
                    score_per_question = paper.total_score / records.count()
                    record.score_gained = score_per_question * (ai_score / 100)
                    record.ai_score = ai_score  # 保存AI原始分数
                    record.is_correct = ai_score >= 60  # 60分以上算合格
                    print(f"[AI评分] 保存到数据库 - ai_score: {record.ai_score}, score_gained: {record.score_gained}, is_correct: {record.is_correct}")
                else:
                    # 客观题：result是布尔值
                    is_correct = result
                    record.is_correct = is_correct
                    score_per_question = paper.total_score / records.count()
                    record.score_gained = score_per_question if is_correct else 0

                total_score += record.score_gained

                # 统计各标签的得分情况（只统计能力类标签）
                for tag in record.question.tags.all():
                    if tag.category not in Tag.ABILITY_CATEGORIES:
                        continue

                    if tag not in tag_scores:
                        tag_scores[tag] = {'correct': 0, 'total': 0}
                    tag_scores[tag]['total'] += 1
                    # 使用record.is_correct来判断是否正确
                    if record.is_correct:
                        tag_scores[tag]['correct'] += 1

                record.save()

            # 更新试卷总分
            paper.score_obtained = total_score
            paper.save()

            # 更新能力画像
            self._update_capability_profiles(paper.user, tag_scores)

        return {
            'paper_id': paper.id,
            'total_score': total_score,
            'max_score': paper.total_score,
            'accuracy': total_score / paper.total_score * 100,
            'tag_performance': self._calculate_tag_performance(tag_scores)
        }

    def _check_answer(self, question, user_answer, option_order=None):
        """检查答案是否正确"""
        if not user_answer:
            return False

        # 主观题使用AI评分
        if question.question_type == Question.QuestionType.SUBJECTIVE:
            score = self._ai_grade_subjective(question, user_answer)
            return score

        # 单选、多选：把考生看到的字母还原成原始选项后按集合比较
        if question.question_type in (Question.QuestionType.SINGLE, Question.QuestionType.MULTIPLE):
            return is_choice_correct(question, option_order, user_answer)

        # 判断题自动评分
        # 标准化答案格式
        user_answer = str(user_answer).strip().upper()
        correct_answer = str(question.correct_answer).strip().upper()

        return user_answer == correct_answer

    def _update_capability_profiles(self, user, tag_scores):
        """更新用户能力画像"""
        weight_old = self.settings['CAPABILITY_UPDATE_WEIGHT_OLD']
        weight_new = self.settings['CAPABILITY_UPDATE_WEIGHT_NEW']

        for tag, score_data in tag_scores.items():
            # 计算当前该标签的准确率
            current_accuracy = score_data['correct'] / score_data['total']

            # 获取或创建能力画像记录
            profile, created = CapabilityProfile.objects.get_or_create(
                user=user,
                tag=tag,
                defaults={'mastery_level': 50.0}
            )

            if created:
                # 新标签，直接基于当前表现设置初始值
                new_score = current_accuracy * 100
            else:
                # 已有标签，使用加权移动平均
                old_score = profile.mastery_level
                new_score = (old_score * weight_old) + (current_accuracy * 100 * weight_new)

            # 确保分数在0-100范围内
            profile.mastery_level = max(0, min(100, new_score))
            profile.save()

    def _ai_grade_subjective(self, question, user_answer):
        """使用AI对主观题进行评分"""
        print(f"[AI评分] 开始对主观题ID:{question.id}进行评分")

        # 检查是否启用AI评分
        if not self.ai_settings.get('ENABLED', False):
            print(f"[AI评分] AI评分功能已禁用，返回默认分数: {self.ai_settings.get('FALLBACK_SCORE', 60)}")
            return self.ai_settings.get('FALLBACK_SCORE', 60)

        print(f"[AI评分] AI评分功能已启用，准备调用API...")
        print(f"[AI评分] 使用模型: {self.ai_settings.get('MODEL_NAME', 'gpt-3.5-turbo')}")

        # 构建评分提示词
        prompt = self.ai_settings.get('PROMPT_TEMPLATE', '').format(
            question=question.content,
            reference_answer=question.correct_answer,  # 复用correct_answer字段存储参考答案
            user_answer=user_answer
        )

        # 准备API请求
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.ai_settings.get("API_KEY", "")}'
        }

        data = {
            'model': self.ai_settings.get('MODEL_NAME', 'gpt-3.5-turbo'),
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,  # 降低随机性，提高评分一致性
            'max_tokens': 10  # 只需要返回一个数字
        }

        try:
            print(f"[AI评分] 发送请求到: {self.ai_settings.get('BASE_URL', 'https://api.openai.com/v1')}/chat/completions")
            # 发送请求
            response = requests.post(
                f'{self.ai_settings.get("BASE_URL", "https://api.openai.com/v1")}/chat/completions',
                headers=headers,
                json=data,
                timeout=self.ai_settings.get('TIMEOUT', 30)
            )

            print(f"[AI评分] 响应状态码: {response.status_code}")
            response.raise_for_status()
            result = response.json()

            # 提取评分结果
            score_text = result['choices'][0]['message']['content'].strip()
            print(f"[AI评分] API返回原始内容: {score_text}")

            # 尝试解析分数
            try:
                score = float(score_text)
                # 确保分数在0-100范围内
                score = max(0, min(100, score))
                print(f"[AI评分] 解析成功，最终分数: {score}")
                return score
            except (ValueError, TypeError) as e:
                print(f"[AI评分] 解析分数失败: {str(e)}，返回默认分数: {self.ai_settings.get('FALLBACK_SCORE', 60)}")
                # 解析失败，返回默认分数
                return self.ai_settings.get('FALLBACK_SCORE', 60)

        except Exception as e:
            # 任何错误都返回默认分数
            print(f"[AI评分] API调用失败: {str(e)}，返回默认分数: {self.ai_settings.get('FALLBACK_SCORE', 60)}")
            return self.ai_settings.get('FALLBACK_SCORE', 60)

    def _calculate_tag_performance(self, tag_scores):
        """计算各标签的表现情况"""
        performance = []

        for tag, score_data in tag_scores.items():
            accuracy = score_data['correct'] / score_data['total'] * 100
            performance.append({
                'tag_name': tag.name,
                'correct_count': score_data['correct'],
                'total_count': score_data['total'],
                'accuracy': round(accuracy, 2)
            })

        return performance