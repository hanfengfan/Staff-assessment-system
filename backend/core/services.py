import random
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

    def generate_exam(self, user_id, reason='daily_practice', question_count=None):
        """
        生成智能试卷

        Args:
            user_id: 用户ID
            reason: 生成原因
            question_count: 题目数量，默认使用配置值

        Returns:
            ExamPaper: 生成的试卷对象
        """
        if question_count is None:
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
            candidate_questions, weak_tags, strategy_counts
        )

        # 创建试卷和答题记录
        with transaction.atomic():
            exam_paper = ExamPaper.objects.create(
                user=user,
                generation_reason=reason,
                status=ExamPaper.Status.NOT_STARTED,
                title=f"{user.job_number}的智能考核试卷",
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
        """获取用户的弱项标签（掌握度低于阈值的标签）"""
        threshold = self.settings['WEAK_CAPABILITY_THRESHOLD']

        weak_profiles = CapabilityProfile.objects.filter(
            user=user,
            mastery_level__lt=threshold
        ).select_related('tag')

        return [profile.tag for profile in weak_profiles]

    def _calculate_strategy_counts(self, total_count):
        """计算各种策略的题目数量分配"""
        weak_ratio = self.settings['WEAK_TAG_RATIO']
        random_ratio = self.settings['RANDOM_RATIO']
        new_ratio = self.settings['NEW_QUESTION_RATIO']

        weak_count = int(total_count * weak_ratio)
        random_count = int(total_count * random_ratio)
        new_count = total_count - weak_count - random_count  # 确保总数一致

        return {
            'weak': weak_count,
            'random': random_count,
            'new': new_count
        }

    def _get_candidate_questions(self, user):
        """获取候选题目池，排除用户最近做过的题目"""
        exclude_hours = self.settings['EXCLUDE_RECENT_HOURS']
        cutoff_time = timezone.now() - timedelta(hours=exclude_hours)

        # 获取用户最近做过的题目ID
        recent_question_ids = ExamRecord.objects.filter(
            paper__user=user,
            created_at__gte=cutoff_time
        ).values_list('question_id', flat=True)

        # 获取可用的题目
        return Question.objects.filter(
            is_active=True
        ).exclude(
            id__in=recent_question_ids
        ).prefetch_related('tags')

    def _select_questions_by_strategy(self, candidate_questions, weak_tags, strategy_counts):
        """按策略选择题目"""
        selected_questions = []
        total_needed = sum(strategy_counts.values())

        print(f"候选题目数量: {candidate_questions.count()}")
        print(f"弱项标签: {weak_tags}")
        print(f"策略分配: {strategy_counts}")

        # 1. 弱项强化题目
        if weak_tags and strategy_counts['weak'] > 0:
            weak_questions = candidate_questions.filter(
                tags__in=weak_tags
            ).distinct()
            print(f"弱项题目数量: {weak_questions.count()}")

            weak_selected = self._random_select_questions(
                weak_questions, strategy_counts['weak']
            )
            selected_questions.extend(weak_selected)
            print(f"选择的弱项题目: {[q.id for q in weak_selected]}")

        # 2. 基础巩固题目
        if strategy_counts['random'] > 0:
            # 排除已经选择的弱项题目
            remaining_questions = candidate_questions.exclude(
                id__in=[q.id for q in selected_questions]
            )
            print(f"剩余题目数量: {remaining_questions.count()}")

            random_selected = self._random_select_questions(
                remaining_questions, strategy_counts['random']
            )
            selected_questions.extend(random_selected)
            print(f"选择的随机题目: {[q.id for q in random_selected]}")

        # 3. 新题探索题目（如果还有剩余名额）
        if strategy_counts['new'] > 0:
            # 在剩余题目中随机选择
            remaining_questions = candidate_questions.exclude(
                id__in=[q.id for q in selected_questions]
            )
            print(f"新题剩余题目数量: {remaining_questions.count()}")

            new_selected = self._random_select_questions(
                remaining_questions, strategy_counts['new']
            )
            selected_questions.extend(new_selected)
            print(f"选择的新题: {[q.id for q in new_selected]}")

        # 4. 容错机制：如果选择的题目不够，从剩余题目中补充
        if len(selected_questions) < total_needed:
            remaining_count = total_needed - len(selected_questions)
            remaining_questions = candidate_questions.exclude(
                id__in=[q.id for q in selected_questions]
            )
            print(f"需要补充{remaining_count}道题目，剩余可用题目: {remaining_questions.count()}")

            if remaining_questions.count() > 0:
                backup_questions = self._random_select_questions(
                    remaining_questions, remaining_count
                )
                selected_questions.extend(backup_questions)
                print(f"补充的题目: {[q.id for q in backup_questions]}")

        # 5. 极端情况：如果没有任何题目，放宽限制
        if len(selected_questions) == 0:
            print("极端情况：放宽所有限制，获取所有可用题目")
            all_questions = Question.objects.filter(is_active=True)
            if all_questions.count() > 0:
                min_count = min(total_needed, all_questions.count())
                emergency_questions = self._random_select_questions(
                    all_questions, min_count
                )
                selected_questions.extend(emergency_questions)
                print(f"紧急选择的题目: {[q.id for q in emergency_questions]}")

        print(f"最终选择的题目总数: {len(selected_questions)}")
        print(f"最终选择的题目ID: {[q.id for q in selected_questions]}")

        # 打乱题目顺序
        random.shuffle(selected_questions)

        return selected_questions

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
                is_correct = self._check_answer(record.question, user_answer)
                record.is_correct = is_correct

                # 简单计分：每题分数相等
                score_per_question = paper.total_score / records.count()
                record.score_gained = score_per_question if is_correct else 0

                if is_correct:
                    total_score += record.score_gained

                # 统计各标签的得分情况
                for tag in record.question.tags.all():
                    if tag not in tag_scores:
                        tag_scores[tag] = {'correct': 0, 'total': 0}
                    tag_scores[tag]['total'] += 1
                    if is_correct:
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