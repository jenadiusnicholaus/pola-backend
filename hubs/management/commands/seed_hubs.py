"""
Seed Topics, Subtopics, and Learning Materials
Management command to populate Legal Education Hub with sample data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from hubs.models import LegalEdTopic, LegalEdSubTopic
from documents.models import LearningMaterial
from authentication.models import PolaUser


class Command(BaseCommand):
    help = 'Seeds topics, subtopics, and learning materials for Legal Education Hub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting to seed Legal Education Hub...'))
        
        if options['clear']:
            self.clear_data()
        
        with transaction.atomic():
            # Get or create admin/lecturer user for materials
            uploader = self.get_uploader()
            
            # Seed data
            topics_data = self.get_topics_data()
            
            for topic_data in topics_data:
                topic = self.create_topic(topic_data)
                
                for subtopic_data in topic_data['subtopics']:
                    subtopic = self.create_subtopic(topic, subtopic_data)
                    
                    # Create materials for this subtopic
                    for material_data in subtopic_data.get('materials', []):
                        self.create_material(subtopic, uploader, material_data)
        
        self.print_summary()
        self.stdout.write(self.style.SUCCESS('\n✅ Seeding completed successfully!'))

    def clear_data(self):
        """Clear existing data"""
        self.stdout.write(self.style.WARNING('Clearing existing data...'))
        
        LearningMaterial.objects.all().delete()
        LegalEdSubTopic.objects.all().delete()
        LegalEdTopic.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

    def get_uploader(self):
        """Get or create uploader user"""
        try:
            # Try to get staff/admin user first
            uploader = PolaUser.objects.filter(is_staff=True).first()
            if not uploader:
                uploader = PolaUser.objects.first()
            
            if not uploader:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                raise Exception('No users available')
            
            return uploader
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting uploader: {e}'))
            raise

    def create_topic(self, data):
        """Create or get topic"""
        topic, created = LegalEdTopic.objects.get_or_create(
            name=data['name'],
            defaults={
                'name_sw': data.get('name_sw', ''),
                'slug': slugify(data['name']),
                'description': data.get('description', ''),
                'description_sw': data.get('description_sw', ''),
                'icon': data.get('icon', '📚'),
                'display_order': data.get('display_order', 0),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created topic: {topic.name}'))
        else:
            self.stdout.write(f'  → Topic exists: {topic.name}')
        
        return topic

    def create_subtopic(self, topic, data):
        """Create or get subtopic"""
        subtopic, created = LegalEdSubTopic.objects.get_or_create(
            topic=topic,
            name=data['name'],
            defaults={
                'name_sw': data.get('name_sw', ''),
                'slug': slugify(data['name']),
                'description': data.get('description', ''),
                'description_sw': data.get('description_sw', ''),
                'display_order': data.get('display_order', 0),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'    ✓ Created subtopic: {subtopic.name}'))
        else:
            self.stdout.write(f'    → Subtopic exists: {subtopic.name}')
        
        return subtopic

    def create_material(self, subtopic, uploader, data):
        """Create or get learning material"""
        material, created = LearningMaterial.objects.get_or_create(
            subtopic=subtopic,
            title=data['title'],
            uploader=uploader,
            defaults={
                'description': data.get('description', ''),
                'category': 'hub_content',
                'language': data.get('language', 'en'),
                'content_type': 'file',
                'price': data.get('price', 0),
                'is_approved': True,
                'is_active': True,
                'uploader_type': 'admin'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'      ✓ Created material: {material.title}'))
        else:
            self.stdout.write(f'      → Material exists: {material.title}')
        
        return material

    def get_topics_data(self):
        """Get sample topics, subtopics, and materials data"""
        return [
            {
                'name': 'Constitutional Law',
                'name_sw': 'Sheria ya Katiba',
                'description': 'Study of constitutional principles, fundamental rights, and government structure',
                'description_sw': 'Masomo ya kanuni za kikatiba, haki za msingi, na muundo wa serikali',
                'icon': '⚖️',
                'display_order': 0,
                'subtopics': [
                    {
                        'name': 'Fundamental Rights and Freedoms',
                        'name_sw': 'Haki na Uhuru wa Msingi',
                        'description': 'Basic human rights guaranteed by the constitution',
                        'description_sw': 'Haki za msingi za binadamu zinazohakikishwa na katiba',
                        'display_order': 0,
                        'materials': [
                            {
                                'title': 'Introduction to Fundamental Rights',
                                'description': 'Overview of fundamental rights in the Tanzanian Constitution',
                                'language': 'en',
                                'price': 0
                            },
                            {
                                'title': 'Right to Life and Personal Liberty',
                                'description': 'Detailed analysis of Article 13 and 14',
                                'language': 'en',
                                'price': 5000
                            }
                        ]
                    },
                    {
                        'name': 'Separation of Powers',
                        'name_sw': 'Mgawanyo wa Mamlaka',
                        'description': 'The three branches of government and their functions',
                        'description_sw': 'Matawi matatu ya serikali na majukumu yao',
                        'display_order': 1,
                        'materials': [
                            {
                                'title': 'Executive Powers and Functions',
                                'description': 'Powers and duties of the President and Cabinet',
                                'language': 'en',
                                'price': 0
                            },
                            {
                                'title': 'Judicial Independence',
                                'description': 'Independence of the judiciary in Tanzania',
                                'language': 'sw',
                                'price': 3000
                            }
                        ]
                    },
                    {
                        'name': 'Constitutional Amendments',
                        'name_sw': 'Marekebisho ya Katiba',
                        'description': 'Process and requirements for amending the constitution',
                        'description_sw': 'Mchakato na mahitaji ya kurekebisha katiba',
                        'display_order': 2,
                        'materials': [
                            {
                                'title': 'Amendment Procedures',
                                'description': 'Step-by-step guide to constitutional amendments',
                                'language': 'en',
                                'price': 0
                            }
                        ]
                    }
                ]
            },
            {
                'name': 'Criminal Law',
                'name_sw': 'Sheria ya Jinai',
                'description': 'Study of crimes, criminal liability, and punishments',
                'description_sw': 'Masomo ya uhalifu, uwajibikaji wa kijinai, na adhabu',
                'icon': '🔨',
                'display_order': 1,
                'subtopics': [
                    {
                        'name': 'General Principles of Criminal Law',
                        'name_sw': 'Kanuni za Jumla za Sheria ya Jinai',
                        'description': 'Fundamental concepts in criminal law',
                        'description_sw': 'Dhana za msingi katika sheria ya jinai',
                        'display_order': 0,
                        'materials': [
                            {
                                'title': 'Elements of a Crime',
                                'description': 'Actus reus and mens rea explained',
                                'language': 'en',
                                'price': 0
                            },
                            {
                                'title': 'Criminal Liability',
                                'description': 'Who can be held criminally responsible',
                                'language': 'en',
                                'price': 4000
                            }
                        ]
                    },
                    {
                        'name': 'Offences Against the Person',
                        'name_sw': 'Makosa Dhidi ya Mtu',
                        'description': 'Murder, assault, and other personal offences',
                        'description_sw': 'Mauaji, mashambulizi, na makosa mengine ya kibinafsi',
                        'display_order': 1,
                        'materials': [
                            {
                                'title': 'Murder and Manslaughter',
                                'description': 'Distinction and legal requirements',
                                'language': 'en',
                                'price': 0
                            },
                            {
                                'title': 'Assault and Battery',
                                'description': 'Types and degrees of assault',
                                'language': 'sw',
                                'price': 3500
                            }
                        ]
                    },
                    {
                        'name': 'Property Offences',
                        'name_sw': 'Makosa ya Mali',
                        'description': 'Theft, robbery, burglary, and related crimes',
                        'description_sw': 'Wizi, unyang\'anyi, uvunjaji, na uhalifu unaohusiana',
                        'display_order': 2,
                        'materials': [
                            {
                                'title': 'Theft and Robbery',
                                'description': 'Legal definitions and distinctions',
                                'language': 'en',
                                'price': 0
                            }
                        ]
                    }
                ]
            },
            {
                'name': 'Contract Law',
                'name_sw': 'Sheria ya Mikataba',
                'description': 'Formation, performance, and enforcement of contracts',
                'description_sw': 'Uundaji, utekelezaji, na utekelezaji wa mikataba',
                'icon': '📝',
                'display_order': 2,
                'subtopics': [
                    {
                        'name': 'Formation of Contracts',
                        'name_sw': 'Uundaji wa Mikataba',
                        'description': 'Essential elements of a valid contract',
                        'description_sw': 'Vipengele muhimu vya mkataba halali',
                        'display_order': 0,
                        'materials': [
                            {
                                'title': 'Offer and Acceptance',
                                'description': 'How contracts are formed',
                                'language': 'en',
                                'price': 0
                            },
                            {
                                'title': 'Consideration',
                                'description': 'The value exchanged in a contract',
                                'language': 'en',
                                'price': 4500
                            }
                        ]
                    },
                    {
                        'name': 'Breach of Contract',
                        'name_sw': 'Uvunjaji wa Mkataba',
                        'description': 'Remedies and damages for breach',
                        'description_sw': 'Masuluhisho na fidia kwa uvunjaji',
                        'display_order': 1,
                        'materials': [
                            {
                                'title': 'Types of Breach',
                                'title_sw': 'Aina za Uvunjaji',
                                'description': 'Material and minor breaches',
                                'language': 'en',
                                'material_type': 'pdf',
                                'is_free': True
                            },
                            {
                                'title': 'Remedies for Breach',
                                'title_sw': 'Masuluhisho kwa Uvunjaji',
                                'description': 'Damages, specific performance, and injunctions',
                                'language': 'sw',
                                'material_type': 'pdf',
                                'price': 5500,
                                'is_free': False
                            }
                        ]
                    }
                ]
            },
            {
                'name': 'Land Law',
                'name_sw': 'Sheria ya Ardhi',
                'description': 'Land ownership, rights, and transactions',
                'description_sw': 'Umiliki wa ardhi, haki, na miamala',
                'icon': '🏠',
                'display_order': 3,
                'subtopics': [
                    {
                        'name': 'Land Tenure Systems',
                        'name_sw': 'Mifumo ya Umiliki wa Ardhi',
                        'description': 'Different types of land ownership',
                        'description_sw': 'Aina mbalimbali za umiliki wa ardhi',
                        'display_order': 0,
                        'materials': [
                            {
                                'title': 'Statutory Rights of Occupancy',
                                'title_sw': 'Haki za Kisheria za Kuishi',
                                'description': 'Granted and deemed rights',
                                'language': 'en',
                                'material_type': 'pdf',
                                'is_free': True
                            },
                            {
                                'title': 'Customary Land Rights',
                                'title_sw': 'Haki za Jadi za Ardhi',
                                'description': 'Traditional land ownership',
                                'language': 'sw',
                                'material_type': 'pdf',
                                'price': 3000,
                                'is_free': False
                            }
                        ]
                    },
                    {
                        'name': 'Land Transactions',
                        'name_sw': 'Miamala ya Ardhi',
                        'description': 'Transfer, lease, and mortgage of land',
                        'description_sw': 'Uhamisho, upangishaji, na rehani ya ardhi',
                        'display_order': 1,
                        'materials': [
                            {
                                'title': 'Land Transfer Procedures',
                                'title_sw': 'Taratibu za Uhamisho wa Ardhi',
                                'description': 'Step-by-step land transfer guide',
                                'language': 'en',
                                'material_type': 'pdf',
                                'is_free': True
                            }
                        ]
                    }
                ]
            },
            {
                'name': 'Company Law',
                'name_sw': 'Sheria ya Makampuni',
                'description': 'Formation and management of companies',
                'description_sw': 'Uundaji na usimamizi wa makampuni',
                'icon': '🏢',
                'display_order': 4,
                'subtopics': [
                    {
                        'name': 'Company Formation',
                        'name_sw': 'Uundaji wa Kampuni',
                        'description': 'Registration and incorporation process',
                        'description_sw': 'Usajili na mchakato wa kuanzisha',
                        'display_order': 0,
                        'materials': [
                            {
                                'title': 'Types of Companies',
                                'title_sw': 'Aina za Makampuni',
                                'description': 'Limited, unlimited, public, and private companies',
                                'language': 'en',
                                'material_type': 'pdf',
                                'is_free': True
                            },
                            {
                                'title': 'Registration Requirements',
                                'title_sw': 'Mahitaji ya Usajili',
                                'description': 'Documents and procedures for registration',
                                'language': 'en',
                                'material_type': 'pdf',
                                'price': 6000,
                                'is_free': False
                            }
                        ]
                    },
                    {
                        'name': 'Directors and Shareholders',
                        'name_sw': 'Wakurugenzi na Wanahisa',
                        'description': 'Rights, duties, and responsibilities',
                        'description_sw': 'Haki, wajibu, na majukumu',
                        'display_order': 1,
                        'materials': [
                            {
                                'title': 'Directors Duties',
                                'title_sw': 'Wajibu wa Wakurugenzi',
                                'description': 'Fiduciary duties and responsibilities',
                                'language': 'en',
                                'material_type': 'pdf',
                                'is_free': True
                            }
                        ]
                    }
                ]
            }
        ]

    def print_summary(self):
        """Print summary of seeded data"""
        topics_count = LegalEdTopic.objects.count()
        subtopics_count = LegalEdSubTopic.objects.count()
        materials_count = LearningMaterial.objects.count()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SEEDING SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'Topics created: {topics_count}')
        self.stdout.write(f'Subtopics created: {subtopics_count}')
        self.stdout.write(f'Materials created: {materials_count}')
        self.stdout.write('='*60)
