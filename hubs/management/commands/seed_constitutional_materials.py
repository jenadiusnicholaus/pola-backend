"""
Seed bilingual learning materials for Constitutional Law (Sheria ya Katiba) subtopics.

Creates/updates LearningMaterial rows (EN + SW) with real article content for:
  - Fundamental Rights and Freedoms
  - Separation of Powers
  - Constitutional Amendments
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from authentication.models import PolaUser
from documents.models import LearningMaterial
from hubs.models import LegalEdSubTopic, LegalEdTopic


class Command(BaseCommand):
    help = 'Seed EN/SW materials for Constitutional Law subtopics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace-stubs',
            action='store_true',
            help='Remove empty stub materials (no content) under these subtopics first',
        )

    def handle(self, *args, **options):
        uploader = PolaUser.objects.filter(is_staff=True).first() or PolaUser.objects.first()
        if not uploader:
            self.stderr.write(self.style.ERROR('No users found. Create a user first.'))
            return

        topic, _ = LegalEdTopic.objects.get_or_create(
            slug='constitutional-law',
            defaults={
                'name': 'Constitutional Law',
                'name_sw': 'Sheria ya Katiba',
                'description': 'Study of constitutional principles, fundamental rights, and government structure',
                'description_sw': 'Masomo ya kanuni za kikatiba, haki za msingi, na muundo wa serikali',
                'icon': '⚖️',
                'display_order': 0,
                'is_active': True,
            },
        )

        created_total = 0
        updated_total = 0

        with transaction.atomic():
            for subtopic_data in self._subtopics_data():
                subtopic, _ = LegalEdSubTopic.objects.get_or_create(
                    topic=topic,
                    name=subtopic_data['name'],
                    defaults={
                        'name_sw': subtopic_data['name_sw'],
                        'slug': slugify(subtopic_data['name']),
                        'description': subtopic_data['description'],
                        'description_sw': subtopic_data['description_sw'],
                        'display_order': subtopic_data['display_order'],
                        'is_active': True,
                        'language': 'en',
                    },
                )

                if options['replace_stubs']:
                    deleted, _ = LearningMaterial.objects.filter(
                        subtopic=subtopic,
                    ).filter(content='').delete()
                    if deleted:
                        self.stdout.write(f'  Removed {deleted} stub material(s) from {subtopic.name}')

                for material in subtopic_data['materials']:
                    for lang, title, description, content in (
                        ('en', material['title'], material['description'], material['content']),
                        ('sw', material['title_sw'], material['description_sw'], material['content_sw']),
                    ):
                        obj, created = LearningMaterial.objects.update_or_create(
                            subtopic=subtopic,
                            title=title,
                            language=lang,
                            defaults={
                                'topic': topic,
                                'uploader': uploader,
                                'uploader_type': 'admin',
                                'hub_type': 'legal_ed',
                                'content_type': material.get('content_type', 'tutorial'),
                                'description': description,
                                'content': content,
                                'price': material.get('price', 0),
                                'is_downloadable': False,
                                'is_approved': True,
                                'is_active': True,
                                'is_verified_quality': True,
                            },
                        )
                        if created:
                            created_total += 1
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Created [{lang}] {title}'))
                        else:
                            updated_total += 1
                            self.stdout.write(f'  → Updated [{lang}] {title}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created {created_total}, updated {updated_total}.'
        ))
        for subtopic in topic.subtopics.filter(is_active=True).order_by('display_order'):
            count = subtopic.materials.filter(is_active=True, is_approved=True).count()
            self.stdout.write(f'  {subtopic.name_sw or subtopic.name}: {count} materials')

    def _subtopics_data(self):
        return [
            {
                'name': 'Fundamental Rights and Freedoms',
                'name_sw': 'Haki na Uhuru wa Msingi',
                'description': 'Basic human rights guaranteed by the constitution',
                'description_sw': 'Haki za msingi za binadamu zinazohakikishwa na katiba',
                'display_order': 0,
                'materials': [
                    {
                        'title': 'Introduction to Fundamental Rights',
                        'title_sw': 'Utangulizi wa Haki za Msingi',
                        'description': 'Overview of fundamental rights in the Constitution of the United Republic of Tanzania',
                        'description_sw': 'Muhtasari wa haki za msingi katika Katiba ya Jamhuri ya Muungano wa Tanzania',
                        'content_type': 'tutorial',
                        'price': 0,
                        'content': """
<h2>Introduction to Fundamental Rights</h2>
<p>Fundamental rights are the basic entitlements that every person enjoys under the Constitution of the United Republic of Tanzania. They protect dignity, equality, and freedom from unlawful interference by the State or other persons.</p>
<h3>Why they matter</h3>
<ul>
  <li>They set minimum standards for how government must treat people.</li>
  <li>They guide courts when interpreting laws and government action.</li>
  <li>They support democracy, the rule of law, and human dignity.</li>
</ul>
<h3>Key ideas</h3>
<p>Rights are not absolute. The Constitution allows limitations that are lawful, necessary, and proportionate — for example to protect public safety, the rights of others, or national security. Any restriction must still respect the spirit of the Bill of Rights.</p>
<p>In this module you will learn how rights are structured, how they are enforced, and how courts balance individual freedoms with public interest.</p>
""".strip(),
                        'content_sw': """
<h2>Utangulizi wa Haki za Msingi</h2>
<p>Haki za msingi ni stahiki muhimu ambazo kila mtu anazo chini ya Katiba ya Jamhuri ya Muungano wa Tanzania. Zinalinda utu, usawa, na uhuru dhidi ya kuingiliwa kinyume cha sheria na Serikali au watu wengine.</p>
<h3>Kwa nini ni muhimu</h3>
<ul>
  <li>Zinaweka viwango vya chini vya jinsi Serikali inavyotakiwa kuwatendea wananchi.</li>
  <li>Zinaongoza mahakama wakati wa kutafsiri sheria na maamuzi ya Serikali.</li>
  <li>Zinaimarisha demokrasia, utawala wa sheria, na utu wa binadamu.</li>
</ul>
<h3>Mawazo muhimu</h3>
<p>Haki si za milele bila mipaka. Katiba inaruhusu vikwazo vilivyo halali, muhimu, na vya uwiano — kwa mfano kulinda usalama wa umma, haki za wengine, au usalama wa taifa. Kikwazo chochote kinapaswa kuheshimu roho ya Hati ya Haki.</p>
<p>Katika somo hili utajifunza jinsi haki zinavyopangwa, jinsi zinavyotekelezwa, na jinsi mahakama zinavyosawazisha uhuru wa mtu na maslahi ya umma.</p>
""".strip(),
                    },
                    {
                        'title': 'Right to Life and Personal Liberty',
                        'title_sw': 'Haki ya Kuishi na Uhuru wa Binafsi',
                        'description': 'Protection of life and personal liberty under the Constitution',
                        'description_sw': 'Ulinzi wa maisha na uhuru wa binafsi chini ya Katiba',
                        'content_type': 'article',
                        'price': 0,
                        'content': """
<h2>Right to Life and Personal Liberty</h2>
<p>The right to life is among the most important constitutional guarantees. Closely linked to it is personal liberty — freedom from arbitrary arrest, detention, or restriction of movement.</p>
<h3>Core protections</h3>
<ul>
  <li><strong>Right to life:</strong> No person may be deprived of life except in accordance with due process of law.</li>
  <li><strong>Personal liberty:</strong> Arrest and detention must follow lawful procedure, including being informed of reasons and access to legal representation.</li>
  <li><strong>Dignity:</strong> Even when liberty is lawfully restricted, persons must be treated humanely.</li>
</ul>
<h3>Practical examples</h3>
<p>Unlawful detention without charge, torture, or denial of bail without legal basis can violate these rights. Courts may grant remedies such as habeas corpus, damages, or orders compelling release or proper process.</p>
<p>Study tip: always ask (1) Is there a law authorizing the action? (2) Was the correct procedure followed? (3) Was the restriction proportionate?</p>
""".strip(),
                        'content_sw': """
<h2>Haki ya Kuishi na Uhuru wa Binafsi</h2>
<p>Haki ya kuishi ni moja ya dhamana muhimu zaidi za kikatiba. Inahusiana kwa karibu na uhuru wa binafsi — uhuru kutokana na kukamatwa, kuzuiliwa, au kuzuia mwendo bila sababu halali.</p>
<h3>Ulinzi wa msingi</h3>
<ul>
  <li><strong>Haki ya kuishi:</strong> Hakuna mtu anayepaswa kunyimwa maisha isipokuwa kwa mujibu wa utaratibu wa sheria.</li>
  <li><strong>Uhuru wa binafsi:</strong> Kukamata na kuzuilia kunapaswa kufuata taratibu za kisheria, ikiwemo kuambiwa sababu na kupata mwakilishi wa kisheria.</li>
  <li><strong>Utu:</strong> Hata uhuru ukizuiliwa kwa mujibu wa sheria, mtu anapaswa kutendewa kwa heshima.</li>
</ul>
<h3>Mifano ya vitendo</h3>
<p>Kuzuiliwa kinyume cha sheria bila shtaka, mateso, au kukataa dhamana bila msingi wa kisheria kunaweza kukiuka haki hizi. Mahakama inaweza kutoa suluhu kama habeas corpus, fidia, au amri za kuachiliwa au kufuata taratibu sahihi.</p>
<p>Kidokezo cha kujifunza: jiulize daima (1) Je, kuna sheria inayoruhusu tendo hilo? (2) Je, taratibu sahihi zilifuatiwa? (3) Je, kikwazo kilikuwa cha uwiano?</p>
""".strip(),
                    },
                    {
                        'title': 'Equality and Non-Discrimination',
                        'title_sw': 'Usawa na Kutobagua',
                        'description': 'Equality before the law and protection against unfair discrimination',
                        'description_sw': 'Usawa mbele ya sheria na ulinzi dhidi ya ubaguzi usio wa haki',
                        'content_type': 'article',
                        'price': 0,
                        'content': """
<h2>Equality and Non-Discrimination</h2>
<p>Equality before the law means every person is entitled to the same legal protection, without unfair distinction based on status, sex, religion, tribe, political opinion, or similar grounds.</p>
<h3>What equality requires</h3>
<ul>
  <li>Equal access to courts and public services.</li>
  <li>Laws and policies that do not arbitrarily favor or exclude groups.</li>
  <li>Remedies when discrimination causes harm.</li>
</ul>
<h3>Important distinction</h3>
<p>Not every difference in treatment is unlawful. Affirmative measures or classifications may be valid if they pursue a legitimate aim and are reasonably connected to that aim. Arbitrary or humiliating distinctions are unconstitutional.</p>
""".strip(),
                        'content_sw': """
<h2>Usawa na Kutobagua</h2>
<p>Usawa mbele ya sheria maana yake kila mtu anastahili ulinzi sawa wa kisheria, bila ubaguzi usio wa haki kwa msingi wa hadhi, jinsia, dini, kabila, maoni ya kisiasa, au sababu zinazofanana.</p>
<h3>Usawa unahitaji nini</h3>
<ul>
  <li>Upatikanaji sawa wa mahakama na huduma za umma.</li>
  <li>Sheria na sera zisizopendelea au kuwatenga watu kiholela.</li>
  <li>Suluhu pale ubaguzi unaposababisha madhara.</li>
</ul>
<h3>Tofauti muhimu</h3>
<p>Si kila tofauti ya matibabu ni kinyume cha sheria. Hatua za kuwawezesha au uainishaji unaweza kuwa halali ikiwa unalenga lengo halali na una uhusiano wa busara na lengo hilo. Ubaguzi wa kiholela au unaodhalilisha ni kinyume cha Katiba.</p>
""".strip(),
                    },
                ],
            },
            {
                'name': 'Separation of Powers',
                'name_sw': 'Mgawanyo wa Mamlaka',
                'description': 'The three branches of government and their functions',
                'description_sw': 'Matawi matatu ya serikali na majukumu yao',
                'display_order': 1,
                'materials': [
                    {
                        'title': 'The Three Branches of Government',
                        'title_sw': 'Matawi Matatu ya Serikali',
                        'description': 'Legislature, Executive, and Judiciary under the Constitution',
                        'description_sw': 'Bunge, Utendaji, na Mahakama chini ya Katiba',
                        'content_type': 'tutorial',
                        'price': 0,
                        'content': """
<h2>The Three Branches of Government</h2>
<p>Separation of powers divides state authority among three main branches so that no single organ monopolizes power.</p>
<ol>
  <li><strong>Legislature (Parliament):</strong> Makes laws, debates national issues, and oversees the Executive.</li>
  <li><strong>Executive:</strong> Implements and administers laws; led by the President and government.</li>
  <li><strong>Judiciary:</strong> Interprets laws and resolves disputes independently and impartially.</li>
</ol>
<h3>Why separation matters</h3>
<p>It prevents tyranny, promotes accountability, and protects rights. Each branch has its own mandate, but they also check and balance one another.</p>
""".strip(),
                        'content_sw': """
<h2>Matawi Matatu ya Serikali</h2>
<p>Mgawanyo wa mamlaka hugawa mamlaka ya dola kati ya matawi matatu kuu ili chombo kimoja kisimiliki mamlaka yote.</p>
<ol>
  <li><strong>Bunge:</strong> Linatunga sheria, linajadili masuala ya taifa, na linasimamia Utendaji.</li>
  <li><strong>Utendaji:</strong> Unatekeleza na kusimamia sheria; unaongozwa na Rais na serikali.</li>
  <li><strong>Mahakama:</strong> Zinatafsiri sheria na kutatua migogoro kwa uhuru na kutopendelea.</li>
</ol>
<h3>Kwa nini mgawanyo ni muhimu</h3>
<p>Unazuia udhalimu, unakuza uwajibikaji, na unalinda haki. Kila tawi lina wajibu wake, lakini pia yanakagana na kusawazishana.</p>
""".strip(),
                    },
                    {
                        'title': 'Executive Powers and Functions',
                        'title_sw': 'Mamlaka na Majukumu ya Utendaji',
                        'description': 'Powers and duties of the President and the Executive',
                        'description_sw': 'Mamlaka na wajibu wa Rais na Utendaji',
                        'content_type': 'article',
                        'price': 0,
                        'content': """
<h2>Executive Powers and Functions</h2>
<p>The Executive is responsible for day-to-day governance: policy implementation, public administration, security, and foreign affairs (as provided by law and the Constitution).</p>
<h3>Typical executive functions</h3>
<ul>
  <li>Assenting to and implementing Acts of Parliament.</li>
  <li>Appointing certain public officers according to constitutional procedures.</li>
  <li>Managing ministries, agencies, and public services.</li>
  <li>Maintaining peace, order, and good government within constitutional limits.</li>
</ul>
<h3>Limits</h3>
<p>Executive power is not unlimited. It must respect the Constitution, Acts of Parliament, court decisions, and fundamental rights. Abuse of power can be challenged through political oversight, courts, or other constitutional mechanisms.</p>
""".strip(),
                        'content_sw': """
<h2>Mamlaka na Majukumu ya Utendaji</h2>
<p>Utendaji unawajibika kwa utawala wa kila siku: utekelezaji wa sera, utawala wa umma, usalama, na mambo ya nje (kama ilivyoainishwa na sheria na Katiba).</p>
<h3>Majukumu ya kawaida ya utendaji</h3>
<ul>
  <li>Kuidhinisha na kutekeleza Sheria za Bunge.</li>
  <li>Kuteua baadhi ya viongozi wa umma kwa mujibu wa taratibu za kikatiba.</li>
  <li>Kusimamia wizara, mamlaka, na huduma za umma.</li>
  <li>Kudumisha amani, utulivu, na utawala bora ndani ya mipaka ya Katiba.</li>
</ul>
<h3>Mipaka</h3>
<p>Mamlaka ya Utendaji siyo yasiyo na kikomo. Lazima iheshimu Katiba, Sheria za Bunge, maamuzi ya mahakama, na haki za msingi. Matumizi mabaya ya mamlaka yanaweza kupingwa kupitia usimamizi wa kisiasa, mahakama, au mifumo mingine ya kikatiba.</p>
""".strip(),
                    },
                    {
                        'title': 'Judicial Independence',
                        'title_sw': 'Uhuru wa Mahakama',
                        'description': 'Independence of the judiciary and its constitutional role',
                        'description_sw': 'Uhuru wa mahakama na jukumu lake la kikatiba',
                        'content_type': 'article',
                        'price': 0,
                        'content': """
<h2>Judicial Independence</h2>
<p>An independent judiciary is essential for the rule of law. Judges must decide cases based on the Constitution and the law, free from improper pressure by the Executive, Legislature, or private interests.</p>
<h3>Pillars of independence</h3>
<ul>
  <li>Security of tenure and proper appointment procedures.</li>
  <li>Financial and administrative arrangements that protect impartiality.</li>
  <li>Freedom to interpret the Constitution and review unlawful acts.</li>
</ul>
<h3>Checks and balances</h3>
<p>Independence does not mean lack of accountability. Judges are bound by the law, ethics, and lawful disciplinary processes. Their independence exists to protect justice for the people, not personal privilege.</p>
""".strip(),
                        'content_sw': """
<h2>Uhuru wa Mahakama</h2>
<p>Mahakama huru ni muhimu kwa utawala wa sheria. Waamuzi wanapaswa kuamua kesi kwa msingi wa Katiba na sheria, bila shinikizo lisilofaa kutoka Utendaji, Bunge, au maslahi binafsi.</p>
<h3>Nguzo za uhuru</h3>
<ul>
  <li>Uhakika wa muda wa ofisi na taratibu sahihi za uteuzi.</li>
  <li>Mipango ya kifedha na kiutawala inayolinda kutopendelea.</li>
  <li>Uhuru wa kutafsiri Katiba na kukagua vitendo visivyo halali.</li>
</ul>
<h3>Ukaguzi na uwiano</h3>
<p>Uhuru hausemi kukosekana kwa uwajibikaji. Waamuzi wamefungwa na sheria, maadili, na taratibu halali za nidhamu. Uhuru wao upo kulinda haki kwa wananchi, siyo privilege binafsi.</p>
""".strip(),
                    },
                ],
            },
            {
                'name': 'Constitutional Amendments',
                'name_sw': 'Marekebisho ya Katiba',
                'description': 'Process and requirements for amending the constitution',
                'description_sw': 'Mchakato na mahitaji ya kurekebisha katiba',
                'display_order': 2,
                'materials': [
                    {
                        'title': 'Why Constitutions Are Amended',
                        'title_sw': 'Kwa Nini Katiba Hurekebishwa',
                        'description': 'Reasons societies update constitutional rules over time',
                        'description_sw': 'Sababu jamii zinavyosasisha kanuni za kikatiba kwa muda',
                        'content_type': 'tutorial',
                        'price': 0,
                        'content': """
<h2>Why Constitutions Are Amended</h2>
<p>A constitution is meant to be stable, but not frozen. Societies amend constitutions to respond to political change, correct gaps, strengthen rights, or reorganize government structures.</p>
<h3>Common reasons</h3>
<ul>
  <li>Expand or clarify fundamental rights.</li>
  <li>Reform elections, terms of office, or institutional powers.</li>
  <li>Resolve conflicts between existing provisions.</li>
  <li>Reflect major national agreements or reforms.</li>
</ul>
<p>Because amendments change the highest law, they usually require a stricter process than ordinary legislation.</p>
""".strip(),
                        'content_sw': """
<h2>Kwa Nini Katiba Hurekebishwa</h2>
<p>Katiba inapaswa kuwa thabiti, lakini siyo isiyobadilika. Jamii hurekebisha katiba ili kukabiliana na mabadiliko ya kisiasa, kurekebisha mapungufu, kuimarisha haki, au kupanga upya miundo ya serikali.</p>
<h3>Sababu za kawaida</h3>
<ul>
  <li>Kupanua au kufafanua haki za msingi.</li>
  <li>Kurekebisha uchaguzi, muda wa ofisi, au mamlaka ya taasisi.</li>
  <li>Kutatua migongano kati ya vifungu vilivyopo.</li>
  <li>Kutoa taswira ya makubaliano au mageuzi makubwa ya kitaifa.</li>
</ul>
<p>Kwa sababu marekebisho yanabadilisha sheria ya juu, kawaida yanahitaji mchakato mkali zaidi kuliko sheria za kawaida.</p>
""".strip(),
                    },
                    {
                        'title': 'Amendment Procedures',
                        'title_sw': 'Taratibu za Marekebisho',
                        'description': 'Step-by-step guide to constitutional amendment procedures',
                        'description_sw': 'Mwongozo wa hatua kwa hatua wa taratibu za kurekebisha katiba',
                        'content_type': 'article',
                        'price': 0,
                        'content': """
<h2>Amendment Procedures</h2>
<p>Constitutional amendment procedures are designed to ensure careful debate and broad legitimacy. Exact steps depend on the constitutional text, but typically include:</p>
<ol>
  <li><strong>Proposal:</strong> A bill or proposal to amend specific articles is introduced.</li>
  <li><strong>Parliamentary process:</strong> Debate, committee review, and voting — often with a special majority.</li>
  <li><strong>Additional approval (where required):</strong> Some amendments may require referendum or other special consent.</li>
  <li><strong>Assent and publication:</strong> Formal approval and publication so the change becomes law.</li>
</ol>
<h3>Study focus</h3>
<p>Learn which provisions are harder to amend, what majority is required, and whether public participation or a referendum is needed for certain changes.</p>
""".strip(),
                        'content_sw': """
<h2>Taratibu za Marekebisho</h2>
<p>Taratibu za kurekebisha Katiba zimeundwa kuhakikisha majadiliano makini na uhalali mpana. Hatua sahihi zinategemea maandishi ya Katiba, lakini kwa kawaida zinajumuisha:</p>
<ol>
  <li><strong>Pendekezo:</strong> Muswada au pendekezo la kurekebisha vifungu maalum linawasilishwa.</li>
  <li><strong>Mchakato wa Bunge:</strong> Majadiliano, ukaguzi wa kamati, na kura — mara nyingi kwa wingi maalum.</li>
  <li><strong>Idhini ya ziada (inapohitajika):</strong> Baadhi ya marekebisho yanaweza kuhitaji kura ya maoni au idhini nyingine maalum.</li>
  <li><strong>Idhini na uchapishaji:</strong> Idhini rasmi na uchapishaji ili mabadiliko yawe sheria.</li>
</ol>
<h3>Lengo la kujifunza</h3>
<p>Jifunze ni vifungu gani ni vigumu zaidi kurekebisha, wingi gani wa kura unahitajika, na kama ushiriki wa umma au kura ya maoni inahitajika kwa mabadiliko fulani.</p>
""".strip(),
                    },
                    {
                        'title': 'Limits on Constitutional Change',
                        'title_sw': 'Mipaka ya Mabadiliko ya Kikatiba',
                        'description': 'Entrenched clauses, democracy, and limits on amending power',
                        'description_sw': 'Vifungu vilivyolindwa, demokrasia, na mipaka ya mamlaka ya kurekebisha',
                        'content_type': 'case_study',
                        'price': 0,
                        'content': """
<h2>Limits on Constitutional Change</h2>
<p>Even the power to amend a constitution may have limits. Some provisions are entrenched — meaning they require higher majorities or special procedures. Courts and scholars also debate whether amendments can destroy the basic structure of constitutional democracy.</p>
<h3>Questions to ask</h3>
<ul>
  <li>Does the amendment follow the correct procedure?</li>
  <li>Does it undermine core democratic principles or fundamental rights?</li>
  <li>Was there meaningful public and parliamentary scrutiny?</li>
</ul>
<p>Understanding these limits helps protect the Constitution as a living charter of self-government, not merely a document that can be rewritten at will.</p>
""".strip(),
                        'content_sw': """
<h2>Mipaka ya Mabadiliko ya Kikatiba</h2>
<p>Hata mamlaka ya kurekebisha Katiba yanaweza kuwa na mipaka. Baadhi ya vifungu vimeimarishwa — maana yanahitaji wingi wa juu wa kura au taratibu maalum. Mahakama na wataalamu pia hujadili kama marekebisho yanaweza kuharibu muundo wa msingi wa demokrasia ya kikatiba.</p>
<h3>Maswali ya kujiuliza</h3>
<ul>
  <li>Je, marekebisho yamefuata taratibu sahihi?</li>
  <li>Je, yanaweza kudhoofisha kanuni za msingi za demokrasia au haki za msingi?</li>
  <li>Je, kulikuwa na uchunguzi wa maana wa umma na Bunge?</li>
</ul>
<p>Kuelewa mipaka hii husaidia kulinda Katiba kama hati hai ya kujitawala, siyo tu hati inayoweza kuandikwa upya kiholela.</p>
""".strip(),
                    },
                ],
            },
        ]
