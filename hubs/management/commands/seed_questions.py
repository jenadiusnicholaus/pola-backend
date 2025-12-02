"""
Django management command to seed sample legal questions for testing admin panel

Usage:
    python manage.py seed_questions
    python manage.py seed_questions --count=50
    python manage.py seed_questions --clear
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from documents.models import LearningMaterial, MaterialQuestion
from django.db import transaction
from django.utils import timezone
import random
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed sample legal questions for admin panel testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=30,
            help='Number of questions to create (default: 30)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing questions before seeding'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing questions...'))
            MaterialQuestion.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared all questions'))

        # Sample legal questions grouped by topic
        questions_by_topic = {
            'Contract Law': [
                'What is the statute of limitations for breach of contract in Tanzania?',
                'Can a contract be valid if one party was under duress?',
                'What are the essential elements of a valid contract?',
                'How can I enforce a verbal agreement in court?',
                'What is the difference between void and voidable contracts?',
                'Can minors enter into legally binding contracts?',
                'What remedies are available for breach of contract?',
                'Is consideration always required for a contract to be valid?',
                'How do I prove a contract existed without written documentation?',
                'What constitutes frustration of contract?',
            ],
            'Criminal Law': [
                'What is the burden of proof in criminal cases?',
                'Can I represent myself in a criminal trial?',
                'What are the differences between theft and robbery?',
                'How long can police detain a suspect without charges?',
                'What rights do I have if arrested?',
                'What is the difference between bail and bond?',
                'Can evidence obtained illegally be used in court?',
                'What constitutes self-defense under Tanzanian law?',
                'How are juvenile offenders treated differently from adults?',
                'What is the appeals process for criminal convictions?',
            ],
            'Family Law': [
                'What are the legal requirements for marriage in Tanzania?',
                'How is property divided in a divorce?',
                'What factors determine child custody decisions?',
                'Can I get a divorce without my spouse\'s consent?',
                'What is the process for legal adoption in Tanzania?',
                'How is child support calculated?',
                'What are the rights of customary law wives?',
                'Can inheritance be challenged in court?',
                'What is the difference between legal separation and divorce?',
                'How do I apply for a protection order?',
            ],
            'Land Law': [
                'What is the difference between granted right of occupancy and customary rights?',
                'How do I register a land title in Tanzania?',
                'Can foreigners own land in Tanzania?',
                'What happens if someone builds on my land without permission?',
                'How long does adverse possession take to establish ownership?',
                'What is the process for land subdivision?',
                'Can the government compulsorily acquire my land?',
                'How do I resolve a boundary dispute with my neighbor?',
                'What documents are needed for land transfer?',
                'What are the rights of tenants on village land?',
            ],
            'Employment Law': [
                'What constitutes unfair dismissal?',
                'How much notice must an employer give for termination?',
                'Am I entitled to severance pay if I resign?',
                'What is the minimum wage in Tanzania?',
                'Can my employer reduce my salary without consent?',
                'What are my rights regarding maternity leave?',
                'How do I file a labor dispute?',
                'Is overtime pay mandatory?',
                'What constitutes workplace harassment?',
                'Can I be fired for joining a trade union?',
            ],
            'Constitutional Law': [
                'What are the fundamental rights guaranteed by the Constitution?',
                'How can I challenge a law as unconstitutional?',
                'What is the process for amending the Constitution?',
                'What powers does the President have under the Constitution?',
                'How does judicial review work in Tanzania?',
                'What is the role of the Attorney General?',
                'Can the government restrict freedom of speech?',
                'What protections exist for minority rights?',
                'How are constitutional disputes resolved?',
                'What is the separation of powers principle?',
            ],
        }

        # Sample answers for some questions (to create answered status)
        sample_answers = {
            'What is the statute of limitations': 'The statute of limitations for breach of contract in Tanzania is generally 6 years from the date of breach under the Law of Limitation Act. However, this period may vary depending on the specific type of contract and circumstances.',
            'What are the essential elements': 'The essential elements of a valid contract are: 1) Offer, 2) Acceptance, 3) Consideration, 4) Intention to create legal relations, 5) Capacity to contract, 6) Free consent (no coercion, fraud, or mistake), and 7) Lawful object.',
            'What is the burden of proof': 'In criminal cases, the burden of proof rests on the prosecution, who must prove the accused\'s guilt "beyond reasonable doubt". This is a higher standard than in civil cases, reflecting the serious consequences of criminal conviction.',
            'What are the legal requirements for marriage': 'Legal requirements for marriage in Tanzania include: both parties must be 18+ years old (or 16+ with parental consent), must consent freely, not be within prohibited degrees of relationship, and the marriage must be registered. Different laws apply for civil, religious, and customary marriages.',
            'What is the difference between granted right': 'A granted right of occupancy is a formal title issued by the government (President or Commissioner for Lands) with clear terms and conditions. Customary rights of occupancy are held under customary law in village land, recognized but less formal than granted rights.',
        }

        try:
            with transaction.atomic():
                # Get or create test users
                students = list(User.objects.filter(user_role__role_name='law_student')[:20])
                if not students:
                    self.stdout.write(self.style.WARNING('No law students found. Creating test student...'))
                    # Create a test student if none exist
                    from authentication.models import UserRole
                    student_role, _ = UserRole.objects.get_or_create(role_name='law_student')
                    test_student = User.objects.create_user(
                        email='test.student@example.com',
                        password='testpass123',
                        first_name='Test',
                        last_name='Student',
                        user_role=student_role
                    )
                    students = [test_student]

                # Get learning materials
                materials = list(LearningMaterial.objects.all()[:50])
                if not materials:
                    self.stdout.write(self.style.ERROR('No learning materials found. Please seed materials first.'))
                    return

                # Get admin user for answering some questions
                admin_user = User.objects.filter(is_staff=True).first()

                created_count = 0
                answered_count = 0
                closed_count = 0

                # Create questions
                all_questions = []
                for topic, questions in questions_by_topic.items():
                    all_questions.extend(questions)

                # Shuffle for randomness
                random.shuffle(all_questions)
                selected_questions = all_questions[:count]

                for i, question_text in enumerate(selected_questions):
                    asker = random.choice(students)
                    material = random.choice(materials)
                    
                    # Create question with random created date (last 30 days)
                    days_ago = random.randint(0, 30)
                    created_at = timezone.now() - timedelta(days=days_ago)
                    
                    question = MaterialQuestion.objects.create(
                        material=material,
                        asker=asker,
                        question_text=question_text,
                        created_at=created_at,
                        status='open'
                    )
                    created_count += 1

                    # Randomly answer some questions (60% chance)
                    if admin_user and random.random() < 0.6:
                        # Find matching answer
                        answer_text = None
                        for key, answer in sample_answers.items():
                            if key.lower() in question_text.lower():
                                answer_text = answer
                                break
                        
                        if not answer_text:
                            answer_text = f"This is a detailed answer to your question about {topic.lower()}. " \
                                        f"According to Tanzanian law and legal precedent, the relevant statutes " \
                                        f"and case law should be carefully considered. It is recommended to consult " \
                                        f"with a qualified legal professional for specific advice related to your situation."
                        
                        # Answer with date after question was asked
                        hours_later = random.randint(1, 48)
                        question.mark_as_answered(
                            answerer=admin_user,
                            answer_text=answer_text
                        )
                        question.answered_at = created_at + timedelta(hours=hours_later)
                        question.save()
                        answered_count += 1

                        # Add some helpful counts to answered questions
                        question.helpful_count = random.randint(0, 15)
                        question.save()

                    # Randomly close some questions (10% chance for open questions)
                    elif random.random() < 0.1:
                        question.close_question()
                        closed_count += 1

                    # Progress indicator
                    if (i + 1) % 10 == 0:
                        self.stdout.write(f'  Created {i + 1}/{count} questions...')

                self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {created_count} questions'))
                self.stdout.write(self.style.SUCCESS(f'  - {answered_count} answered'))
                self.stdout.write(self.style.SUCCESS(f'  - {closed_count} closed'))
                self.stdout.write(self.style.SUCCESS(f'  - {created_count - answered_count - closed_count} open'))

                # Summary stats
                self.stdout.write('\n' + '='*50)
                self.stdout.write(self.style.WARNING('SUMMARY:'))
                self.stdout.write(f'Total Questions: {MaterialQuestion.objects.count()}')
                self.stdout.write(f'Open: {MaterialQuestion.objects.filter(status="open").count()}')
                self.stdout.write(f'Answered: {MaterialQuestion.objects.filter(status="answered").count()}')
                self.stdout.write(f'Closed: {MaterialQuestion.objects.filter(status="closed").count()}')
                self.stdout.write('='*50)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding questions: {str(e)}'))
            raise
