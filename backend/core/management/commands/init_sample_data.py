from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Tag, Question
from analysis.models import CapabilityProfile
import random

User = get_user_model()


class Command(BaseCommand):
    help = '初始化示例数据：创建测试用户、标签、题目和能力画像'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始初始化示例数据...'))

        # 1. 创建测试用户
        self.create_test_users()

        # 2. 创建标签
        tags = self.create_tags()

        # 3. 创建题目
        self.create_questions(tags)

        # 4. 初始化用户能力画像
        self.initialize_capability_profiles()

        self.stdout.write(self.style.SUCCESS('示例数据初始化完成！'))

    def create_test_users(self):
        """创建测试用户"""
        test_users = [
            {
                'job_number': 'ST001',
                'username': 'zhangsan',
                'first_name': '张',
                'last_name': '三',
                'position': '值班站长',
                'department': '北京西站',
                'password': 'password123'
            },
            {
                'job_number': 'ST002',
                'username': 'lisi',
                'first_name': '李',
                'last_name': '四',
                'position': '站务员',
                'department': '北京西站',
                'password': 'password123'
            },
            {
                'job_number': 'ST003',
                'username': 'wangwu',
                'first_name': '王',
                'last_name': '五',
                'position': '客运值班员',
                'department': '北京南站',
                'password': 'password123'
            }
        ]

        for user_data in test_users:
            user, created = User.objects.get_or_create(
                job_number=user_data['job_number'],
                defaults={
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'position': user_data['position'],
                    'department': user_data['department'],
                    'email': f"{user_data['username']}@railway.com",
                }
            )

            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f"  创建用户: {user.job_number} - {user.get_full_name()}")

    def create_tags(self):
        """创建标签"""
        tags_data = [
            {'name': '票务处理', 'category': 'position', 'description': '包括售票、退票、改签等票务相关操作'},
            {'name': '乘客服务', 'category': 'position', 'description': '乘客咨询、引导、特殊乘客服务等'},
            {'name': '安全检查', 'category': 'position', 'description': '行李检查、安全巡查、危险品识别'},
            {'name': '应急处理', 'category': 'emergency', 'description': '包括火灾预防、报警、疏散、初期扑救及其他突发事件应急响应和处理'},
            {'name': '设备故障', 'category': 'emergency', 'description': '站内设备故障处理和报修流程'},
            {'name': '沟通协调', 'category': 'comprehensive', 'description': '与各部门、同事间的沟通协调能力'},
            {'name': '规章制度', 'category': 'comprehensive', 'description': '铁路相关法律法规和站内管理制度'},
        ]

        tags = []
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'category': tag_data['category'],
                    'description': tag_data['description']
                }
            )
            tags.append(tag)

            if created:
                self.stdout.write(f"  创建标签: {tag.name}")

        return tags

    def create_questions(self, tags):
        """创建示例题目"""
        questions_data = [
            {
                'content': '旅客购买车票后，要求改签，应当如何处理？',
                'question_type': 'single',
                'options': [
                    {'key': 'A', 'text': '直接拒绝改签要求'},
                    {'key': 'B', 'text': '检查车票状态，按规定办理改签手续'},
                    {'key': 'C', 'text': '要求旅客先退票再重新购买'},
                    {'key': 'D', 'text': '告诉旅客改签只能在发车前24小时办理'}
                ],
                'correct_answer': 'B',
                'difficulty': 2,
                'explanation': '应根据铁路客运规程，检查车票是否符合改签条件，并按规定办理改签手续。',
                'tags': ['票务处理']
            },
            {
                'content': '发现乘客携带疑似危险品时，正确的处理方式包括哪些？',
                'question_type': 'multiple',
                'options': [
                    {'key': 'A', 'text': '立即报告车站值班员'},
                    {'key': 'B', 'text': '将乘客带至安全区域进一步检查'},
                    {'key': 'C', 'text': '自行判断后决定是否放行'},
                    {'key': 'D', 'text': '按照规定程序处理，必要时报警'},
                    {'key': 'E', 'text': '为了避免冲突，直接放行'}
                ],
                'correct_answer': 'A,B,D',
                'difficulty': 3,
                'explanation': '发现疑似危险品时，应立即报告值班员，将乘客带至安全区域，按程序处理，必要时报警。不能自行判断或直接放行。',
                'tags': ['安全检查', '应急处理']
            },
            {
                'content': '车站发生火灾时，第一要务是什么？',
                'question_type': 'single',
                'options': [
                    {'key': 'A', 'text': '立即拨打119报警'},
                    {'key': 'B', 'text': '组织乘客疏散撤离'},
                    {'key': 'C', 'text': '使用灭火器灭火'},
                    {'key': 'D', 'text': '关闭车站电源'}
                ],
                'correct_answer': 'B',
                'difficulty': 1,
                'explanation': '火灾发生时，保障乘客生命安全是第一要务，应立即组织乘客有序疏散撤离。',
                'tags': ['应急处理']
            },
            {
                'content': '售票系统出现故障时，应当采取的措施是什么？',
                'question_type': 'true_false',
                'options': [
                    {'key': 'True', 'text': '立即停止售票，报告技术部门，设置临时售票点'},
                    {'key': 'False', 'text': '继续尝试使用故障系统，等待系统自动恢复'}
                ],
                'correct_answer': 'True',
                'difficulty': 2,
                'explanation': '系统故障时应立即停止使用，报告技术部门，并启动应急预案设置临时售票点，确保客运服务不受影响。',
                'tags': ['设备故障', '票务处理']
            },
            {
                'content': '老年乘客行动不便，需要乘车协助，以下做法正确的是？',
                'question_type': 'single',
                'options': [
                    {'key': 'A', 'text': '建议其家属陪同，自己不予过多关注'},
                    {'key': 'B', 'text': '主动提供帮助，协助其安检、进站、上车'},
                    {'key': 'C', 'text': '告知其需要额外付费才能获得协助服务'},
                    {'key': 'D', 'text': '让其自己解决问题，避免发生责任纠纷'}
                ],
                'correct_answer': 'B',
                'difficulty': 1,
                'explanation': '对老年乘客等特殊群体应主动提供帮助服务，体现铁路客运的人文关怀。',
                'tags': ['乘客服务', '沟通协调']
            }
        ]

        for question_data in questions_data:
            question, created = Question.objects.get_or_create(
                content=question_data['content'],
                defaults={
                    'question_type': question_data['question_type'],
                    'options': question_data['options'],
                    'correct_answer': question_data['correct_answer'],
                    'difficulty': question_data['difficulty'],
                    'explanation': question_data['explanation']
                }
            )

            if created:
                # 添加标签
                for tag_name in question_data['tags']:
                    tag = Tag.objects.get(name=tag_name)
                    question.tags.add(tag)

                self.stdout.write(f"  创建题目: {question.content[:30]}...")

    def initialize_capability_profiles(self):
        """初始化用户能力画像"""
        users = User.objects.all()
        tags = Tag.objects.all()

        for user in users:
            for tag in tags:
                # 为每个用户在每个标签下创建随机的能力画像
                # 模拟不同用户的强弱项
                if user.job_number == 'ST001':  # 值班站长，综合能力较强
                    if tag.category in ['position', 'comprehensive']:
                        mastery_level = random.uniform(70, 90)
                    else:  # 应急类稍弱
                        mastery_level = random.uniform(50, 70)
                elif user.job_number == 'ST002':  # 站务员，日常业务熟练
                    if tag.category == 'position':
                        mastery_level = random.uniform(75, 85)
                    else:
                        mastery_level = random.uniform(45, 65)
                else:  # 新员工，整体能力较弱
                    mastery_level = random.uniform(40, 60)

                profile, created = CapabilityProfile.objects.get_or_create(
                    user=user,
                    tag=tag,
                    defaults={'mastery_level': mastery_level}
                )

                if created:
                    self.stdout.write(f"  初始化能力画像: {user.job_number} - {tag.name}: {mastery_level:.1f}")