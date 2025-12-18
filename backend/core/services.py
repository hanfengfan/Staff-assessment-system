import random
import json
import requests
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Question, ExamPaper, ExamRecord
from analysis.models import CapabilityProfile

User = get_user_model()


class ExamGenerationService:
    """智能组卷服务"""

    def __init__(self):
        self.settings = settings.ASSESSMENT_SETTINGS

    def generate_exam(self, user_id, reason='daily_practice'):
        """
        生成智能试卷（题目数量由后端配置控制）

        Args:
            user_id: 用户ID
            reason: 生成原因

        Returns:
            ExamPaper: 生成的试卷对象
        """
        # 使用配置的题目数量，不接受前端参数
        question_count = self.settings['DEFAULT_EXAM_QUESTION_COUNT']

        user = User.objects.get(id=user_id)

        # 获取用户弱项标签
        weak_tags = self._get_weak_tags(user)

        # 获取策略分配
        strategy_counts = self._calculate_strategy_counts(question_count)

        # 获取候选题目池
        candidate_questions = self._get_candidate_questions(user)

        # 按策略抽题
        selected_questions = self._select_questions_by_strategy(
            candidate_questions, weak_tags, strategy_counts, user
        )

        # 确保至少选择了题目
        if not selected_questions:
            print(f"警告：未能为用户 {user_id} 生成任何题目！")
            print(f"候选题目总数: {candidate_questions.count()}")
            print(f"弱项标签: {weak_tags}")
            print(f"策略分配: {strategy_counts}")
        else:
            print(f"成功为用户 {user_id} 选择了 {len(selected_questions)} 道题目")

        # 创建试卷和答题记录
        with transaction.atomic():
            exam_paper = ExamPaper.objects.create(
                user=user,
                generation_reason=reason,
                status=ExamPaper.Status.NOT_STARTED,
                title=f"{user.job_number}的智能考核试卷",
                total_score=100.0,  # 固定100分，根据实际题目数量平均分配
            )

            # 创建答题记录
            for question in selected_questions:
                ExamRecord.objects.create(
                    paper=exam_paper,
                    question=question,
                    score_gained=0.0  # 初始未答题，得分为0
                )

        return exam_paper

    def _get_weak_tags(self, user):
        """获取用户的弱项标签（掌握度低于阈值的标签，排除role标签）"""
        threshold = self.settings['WEAK_CAPABILITY_THRESHOLD']

        weak_profiles = CapabilityProfile.objects.filter(
            user=user,
            mastery_level__lt=threshold
        ).exclude(
            tag__category='role'  # 排除role标签，专注实际能力弱项
        ).select_related('tag')

        return [profile.tag for profile in weak_profiles]

    def _calculate_strategy_counts(self, total_count):
        """计算各种策略的题目数量分配"""
        weak_ratio = self.settings['WEAK_TAG_RATIO']
        new_ratio = self.settings['NEW_QUESTION_RATIO']

        weak_count = int(total_count * weak_ratio)
        new_count = total_count - weak_count  # 确保总数一致

        return {
            'weak': weak_count,
            'new': new_count
        }

    def _get_candidate_questions(self, user):
        """获取候选题目池，排除用户最近做过的题目，并根据用户职位筛选"""
        exclude_hours = self.settings['EXCLUDE_RECENT_HOURS']
        cutoff_time = timezone.now() - timedelta(hours=exclude_hours)

        # 获取用户最近做过的题目ID
        recent_question_ids = ExamRecord.objects.filter(
            paper__user=user,
            created_at__gte=cutoff_time
        ).values_list('question_id', flat=True)

        # 获取可用的题目
        questions = Question.objects.filter(
            is_active=True
        ).exclude(
            id__in=recent_question_ids
        ).prefetch_related('tags')

        # 根据用户职位筛选题目
        # 管理员可以获取所有职位的题目
        if user.position == '系统管理员':
            return questions

        # 尝试根据用户职位找到对应的role标签
        try:
            from .models import Tag
            role_tag = Tag.objects.filter(name=user.position, category='role').first()
            if role_tag:
                # 选择符合用户职位的题目
                questions = questions.filter(tags=role_tag)
            else:
                # 如果没有找到对应的role标签，使用position、emergency、comprehensive分类的题目
                questions = questions.filter(
                    tags__category__in=['position', 'emergency', 'comprehensive']
                ).distinct()
        except Exception as e:
            # 出现异常时，返回所有可用题目作为后备
            pass

        return questions

    def _select_questions_by_strategy(self, candidate_questions, weak_tags, strategy_counts, user):
        """按策略选择题目"""
        selected_questions = []
        total_needed = sum(strategy_counts.values())

        # 0. 优先选择1道该角色对应的主观题
        role_subjective_question = self._get_role_subjective_question(candidate_questions, user)
        if role_subjective_question:
            selected_questions.append(role_subjective_question)
            # 减少新题需要的数量，因为主观题占了一个名额
            if strategy_counts['new'] > 0:
                strategy_counts['new'] -= 1

        # 1. 弱项强化题目
        if weak_tags and strategy_counts['weak'] > 0:
            weak_questions = candidate_questions.filter(
                tags__in=weak_tags
            ).exclude(
                id__in=[q.id for q in selected_questions]
            ).distinct()

            weak_selected = self._random_select_questions(
                weak_questions, strategy_counts['weak']
            )
            selected_questions.extend(weak_selected)

        # 2. 新题探索题目（如果还有剩余名额）
        if strategy_counts['new'] > 0:
            remaining_questions = candidate_questions.exclude(
                id__in=[q.id for q in selected_questions]
            )

            new_selected = self._random_select_questions(
                remaining_questions, strategy_counts['new']
            )
            selected_questions.extend(new_selected)

        # 3. 容错机制：如果选择的题目不够，从剩余题目中补充
        if len(selected_questions) < total_needed:
            remaining_count = total_needed - len(selected_questions)
            remaining_questions = candidate_questions.exclude(
                id__in=[q.id for q in selected_questions]
            )

            if remaining_questions.count() > 0:
                backup_questions = self._random_select_questions(
                    remaining_questions, remaining_count
                )
                selected_questions.extend(backup_questions)

        # 4. 极端情况：如果没有任何题目，放宽限制
        if len(selected_questions) == 0:
            all_questions = Question.objects.filter(is_active=True)
            if all_questions.count() > 0:
                min_count = min(total_needed, all_questions.count())
                emergency_questions = self._random_select_questions(
                    all_questions, min_count
                )
                selected_questions.extend(emergency_questions)

        # 打乱题目顺序
        random.shuffle(selected_questions)

        return selected_questions

    def _get_role_subjective_question(self, candidate_questions, user):
        """获取该角色对应的主观题"""
        try:
            from .models import Tag
            # 管理员可以使用所有主观题
            if user.position == '系统管理员':
                role_questions = candidate_questions.filter(
                    question_type=Question.QuestionType.SUBJECTIVE
                )
            else:
                # 尝试根据用户职位找到对应的role标签
                role_tag = Tag.objects.filter(name=user.position, category='role').first()
                if role_tag:
                    # 查找包含该role标签的主观题
                    role_questions = candidate_questions.filter(
                        tags=role_tag,
                        question_type=Question.QuestionType.SUBJECTIVE
                    )
                else:
                    # 如果没有找到对应的role标签，使用任意主观题
                    role_questions = candidate_questions.filter(
                        question_type=Question.QuestionType.SUBJECTIVE
                    )

            # 随机选择1道
            if role_questions.count() > 0:
                return self._random_select_questions(role_questions, 1)[0]

        except Exception as e:
            # 出现异常时返回None，不影响正常组卷流程
            pass

        return None

    def _random_select_questions(self, questions, count):
        """从题目集合中随机选择指定数量的题目"""
        question_list = list(questions)

        if len(question_list) <= count:
            return question_list

        return random.sample(question_list, count)


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
                result = self._check_answer(record.question, user_answer)

                if record.question.question_type == Question.QuestionType.SUBJECTIVE:
                    # 主观题：result是AI评分的分数(0-100)
                    ai_score = result
                    # 将分数按比例转换为题目得分
                    score_per_question = paper.total_score / records.count()
                    record.score_gained = score_per_question * (ai_score / 100)
                    record.ai_score = ai_score  # 保存AI原始分数
                    record.is_correct = ai_score >= 60  # 60分以上算合格
                else:
                    # 客观题：result是布尔值
                    is_correct = result
                    record.is_correct = is_correct
                    score_per_question = paper.total_score / records.count()
                    record.score_gained = score_per_question if is_correct else 0

                total_score += record.score_gained

                # 统计各标签的得分情况（排除role标签，专注能力维度）
                for tag in record.question.tags.all():
                    # 排除role标签，只统计实际能力相关的标签
                    if tag.category == 'role':
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

    def _check_answer(self, question, user_answer):
        """检查答案是否正确"""
        if not user_answer:
            return False

        # 主观题使用AI评分
        if question.question_type == Question.QuestionType.SUBJECTIVE:
            score = self._ai_grade_subjective(question, user_answer)
            return score

        # 客观题自动评分
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
        # 检查是否启用AI评分
        if not self.ai_settings.get('ENABLED', False):
            return self.ai_settings.get('FALLBACK_SCORE', 60)

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
            # 发送请求
            response = requests.post(
                f'{self.ai_settings.get("BASE_URL", "https://api.openai.com/v1")}/chat/completions',
                headers=headers,
                json=data,
                timeout=self.ai_settings.get('TIMEOUT', 30)
            )

            response.raise_for_status()
            result = response.json()

            # 提取评分结果
            score_text = result['choices'][0]['message']['content'].strip()

            # 尝试解析分数
            try:
                score = float(score_text)
                # 确保分数在0-100范围内
                score = max(0, min(100, score))
                return score
            except (ValueError, TypeError):
                # 解析失败，返回默认分数
                return self.ai_settings.get('FALLBACK_SCORE', 60)

        except Exception as e:
            # 任何错误都返回默认分数
            print(f"AI评分失败: {str(e)}")
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