"""
Management command to seed document content (policies, terms, conditions, etc.)
"""
from django.core.management.base import BaseCommand
from document_templates.models import DocumentContent


class Command(BaseCommand):
    help = 'Seed document content with default policies and terms'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📄 Seeding document content...'))

        # Terms and Conditions
        terms_content = """# TERMS AND CONDITIONS

**Last Updated:** 01/06/2026

Welcome to POLA App.

By accessing or using POLA, you agree to be bound by these Terms and Conditions. If you do not agree with these Terms, please do not use the Platform.

## 1. About the Platform

POLA is a digital platform that provides educational information, AI-assisted guidance, document templates, and access to professional consultation services.

The Platform is intended to improve access to information and professional support.

Information provided through the Platform should not be considered a substitute for independent professional advice.

## 2. Eligibility

You must be at least 18 years old to use the Platform.

You agree to provide accurate and current information when creating an account.

## 3. User Accounts

Users are responsible for maintaining the confidentiality of their account credentials.

You are responsible for all activities conducted through your account.

We reserve the right to suspend or terminate accounts that violate these Terms.

## 4. Acceptable Use

You agree not to:

- Use the Platform for unlawful purposes.
- Upload harmful, abusive, defamatory, or misleading content.
- Attempt to interfere with the operation of the Platform.
- Impersonate another person or organization.
- Use automated systems to access the Platform without authorization.

## 5. AI-Assisted Services

The Platform may provide information generated through artificial intelligence.

AI-generated responses are intended for informational purposes only and may not always be accurate, complete, or suitable for your specific circumstances.

Users should exercise independent judgment and seek professional advice where necessary.

## 6. Professional Consultations

The Platform may facilitate communication between users and independent professionals.

Professionals remain independently responsible for any advice or services they provide.

POLA does not guarantee outcomes arising from consultations.

## 7. Payments

Certain services may require payment.

Prices will be displayed before purchase.

Payments are processed through authorized payment providers.

Users are responsible for ensuring that payment information provided is accurate.

## 8. Intellectual Property

All content, software, logos, trademarks, designs, and materials available on the Platform are owned by and licensed to POLA.

Users may not copy, reproduce, distribute, or exploit any content without permission.

## 9. Service Availability

We strive to maintain uninterrupted service but do not guarantee continuous availability.

We may modify, suspend, or discontinue portions of the Platform at any time.

## 10. Limitation of Liability

To the maximum extent permitted by law, POLA shall not be liable for indirect, incidental, consequential, or special damages arising from use of the Platform.

## 11. Termination

We may suspend or terminate access where users violate these Terms or engage in conduct that may harm the Platform or other users.

## 12. Changes to These Terms

We may update these Terms from time to time.

Continued use of the Platform after updates constitutes acceptance of the revised Terms.

## 13. Contact Information

For questions regarding these Terms, please contact:

- **Email:** polatanzania@gmail.com
- **Company:** Olidox Company Limited
- **Country:** Tanzania
"""

        terms_content_sw = """# SHARTI NA MASHARTI

**Imesasishwa:** 01/06/2026

Karibu kwenye Programu ya POLA.

Kwa kufikia au kutumia POLA, unakubali kuwa chini ya Sharti na Masharti hizi. Ikiwa hukubali Sharti hizi, tafadhali usitumie Jukwaa hili.

## 1. Kuhusu Jukwaa

POLA ni jukwaa la kidijitali linalotoa maelezo ya elimu, mwongozo usaidiwa na AI, mifumo ya waraka, na ufikiaji wa huduma za ushauri wa kitaalamu.

Jukwaa hili linakusudiwa kuboresha ufikiaji wa taarifa na msaada wa kitaalamu.

Maelezo yanayotolewa kupitia Jukwaa hayapaswi kuchukuliwa kama mbadala ya ushauri wa kitaalamu huria.

## 2. Ustahiki

Unapaswa kuwa na umri wa angalau miaka 18 ili kutumia Jukwaa.

Unakubali kutoa taarifa sahihi na za sasa wakati wa kuunda akaunti.

## 3. Akaunti za Watumiaji

Watumiaji wana jukumu la kudumisha siri ya hati zao za akaunti.

Wewe unajumuika kwa shughuli zote zinazofanywa kupitia akaunti yako.

Tuna haki ya kusitisha au kuacha akaunti zinazokiuka Sharti hizi.

## 4. Matumizi Yanayokubalika

Unakubali kutofanya:

- Kutumia Jukwaa kwa madhumuni ya haramu.
- Kupakia maudishi yanayoharibu, yanayosema matusi, au yanayopotosha.
- Kujaribu kuingilia utendaji wa Jukwaa.
- Kujifanya kuwa mtu au shirika lingine.
- Kutumia mifumo ya otomatiki kufikia Jukwaa bila idhini.

## 5. Huduma Zilizosaidiwa na AI

Jukwaa linaweza kutoa maelezo yaliyozalishwa kupitia akili bandia.

Majibu yaliyozalishwa na AI yanakusudiwa kwa madhumuni ya taarifa tu na yanaweza kuwa si sahihi, kamili, au yanayofaa kwa hali zako mahususi.

Watumiaji wanapaswa kutumia hukumu huria na kutafuta ushauri wa kitaalamu pale inapohitajika.

## 6. Ushauri wa Kitaalamu

Jukwaa linaweza kurahisisha mawasiliano kati ya watumiaji na wataalamu huria.

Wataalamu wanabaki wajumuika kwa ushauri au huduma wanazotoa.

POLA hahakikishi matokeo yanayotokana na ushauri.

## 7. Malipo

Huduma fulani zinaweza kuhitaji malipo.

Bei zitawasilishwa kabla ya ununuzi.

Malipo hutolewa kupitia watoa huduma waliodhinishwa.

Watumiaji wana jukumu la kuhakikisha kuwa taarifa ya malipo iliyotolewa ni sahihi.

## 8. Mali ya Akili

Yaliyomo yote, programu, alama, alama za biashara, miundo, na vifaa vinavyopatikana kwenye Jukwaa vimilikiwa na leseniwa kwa POLA.

Watumiaji hawaruhusiwi kunakili, kuzalisha, kusambaza, au kutumia yaliyomo yoyote bila idhini.

## 9. Upatikanaji wa Huduma

Tunajaribu kudumisha huduma isiyokatika lakini hatuhakikishi upatikanaji wa mfululizo.

Tunaweza kubadilisha, kusitisha, au kuacha sehemu za Jukwaa wakati wowote.

## 10. Kikwazo cha Jukumu

Kwa kiwango cha juu kinachoruhusiwa na sheria, POLA haitajumuika kwa hasara za moja kwa moja, za upande, za matokeo, au maalum zinazotokana na matumizi ya Jukwaa.

## 11. Kuisha

Tunaweza kusitisha au kuacha ufikiaji ambapo watumiaji wanakiuka Sharti hizi au wanashiriki katika mwenendo ambao unaweza kuharibu Jukwaa au watumiaji wengine.

## 12. Mabadiliko ya Sharti Hizi

Tunaweza kusasisha Sharti hizi wakati mwingine.

Matumizi yaendeleo ya Jukwaa baada ya sasisho kunakubali kukubali Sharti zilizorekebishwa.

## 13. Maelezo ya Mawasiliano

Kwa maswali kuhusu Sharti hizi, tafadhali wasiliana:

- **Barua pepe:** polatanzania@gmail.com
- **Kampuni:** Olidox Company Limited
- **Nchi:** Tanzania
"""

        doc, created = DocumentContent.objects.update_or_create(
            slug='terms-and-conditions',
            defaults={
                'title': 'Terms and Conditions',
                'title_sw': 'Sharti na Masharti',
                'category': 'terms',
                'content': terms_content,
                'content_sw': terms_content_sw,
                'is_active': True,
                'is_public': True,
                'display_order': 1
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created: {doc.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'↻ Updated: {doc.title}'))

        # Refund Policy
        refund_content = """# REFUND POLICY

**Last Updated:** 01/06/2026

POLA aims to provide fair and transparent payment practices.

## 1. Digital Purchases

Because many services are delivered instantly after purchase, certain purchases may not be refundable once consumed or used.

## 2. Eligible Refund Requests

Refunds may be granted where:

- A user is charged multiple times for the same purchase.
- A technical error prevents access to a purchased service.
- Payment is processed but the service is not delivered.
- Unauthorized transactions are verified.

## 3. Consultation Services

If a scheduled consultation does not occur due to the professional's absence, technical failure, or platform error, users may choose:

- A full refund; or
- Rescheduling of the consultation.

## 4. User Cancellation

Users may cancel future bookings before the scheduled consultation time.

Where a consultation has not yet started, a refund or account credit may be issued.

## 5. Completed Services

Completed consultations and services already delivered are generally not refundable unless required by law or where service quality falls substantially below reasonable expectations.

## 6. Refund Processing Time

Approved refunds will typically be processed within 7–14 business days depending on the payment provider.

## 7. Requesting a Refund

Refund requests may be submitted through:

**Email:** polatanzania@gmail.com

Users should include:

- Account details
- Transaction reference
- Date of payment
- Reason for the request

Each request will be reviewed fairly and individually.
"""

        refund_content_sw = """# SERA YA KURUDISHA MALIPO

**Imesasishwa:** 01/06/2026

POLA inalenga kutoa mazoea ya malipo ya haki na wazi.

## 1. Ununuzi wa Kidijitali

Kwa kuwa huduma nyingi zinatolewa mara moja baada ya ununuzi, ununuzi fulani hauwezi kurudishwa mara moja baada ya kutumika.

## 2. Ombi la Kurudisha Malipo Linalostahiki

Kurudisha malipo kunaweza kutokea ambapo:

- Mtumiaji anatozwa mara nyingi kwa ununuzi moja.
- Hitilafu ya kiufuni inazuia ufikiaji wa huduma ilinunuliwa.
- Malipo yamechakatwa lakini huduma haikujitolewa.
- Muamala usio idhinishwa unathibitishwa.

## 3. Huduma za Ushauri

Ikiwa ushauri uliopangwa hautatokea kwa sababu ya kutokuwepo kwa mtaalamu, hitilafu ya kiufuni, au hitilafu ya jukwaa, watumiaji wanaweza kuchagua:

- Kurudisha malipo kamili; au
- Kuupangia upya ushauri.

## 4. Ukataji wa Mtumiaji

Watumiaji wanaweza kufuta uwekaji wa baadaye kabla ya muda wa ushauri uliopangwa.

Ambapo ushauri bado haujaanza, kurudisha malipo au mkopo wa akaunti unaweza kutolewa.

## 5. Huduma Zilizokamilika

Ushauri uliokamilika na huduma zilizotolewa kwa ujumla hazirudishiwi isipokuwa inahitajika na sheria au ambapo ubora wa huduma umepungua sana chini ya matarajio ya kawaida.

## 6. Muda wa Usindikaji wa Kurudisha Malipo

Kurudisha malipo vilivyoidhinishwa kwa kawaida vitasindikwa ndani ya siku 7–14 za kazi kulingana na mtoaji wa malipo.

## 7. Kuomba Kurudisha Malipo

Ombi la kurudisha malipo linaweza kuwasilishwa kupitia:

**Barua pepe:** polatanzania@gmail.com

Watumiaji wanapaswa kujumuisha:

- Maelezo ya akaunti
- Rejelesi ya muamala
- Tarehe ya malipo
- Sababu ya ombi

Kila ombi litapitiwa kwa haki na kwa mtu binafsi.
"""

        doc, created = DocumentContent.objects.update_or_create(
            slug='refund-policy',
            defaults={
                'title': 'Refund Policy',
                'title_sw': 'Sera ya Kurudisha Malipo',
                'category': 'policy',
                'content': refund_content,
                'content_sw': refund_content_sw,
                'is_active': True,
                'is_public': True,
                'display_order': 2
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created: {doc.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'↻ Updated: {doc.title}'))

        # Privacy Policy
        privacy_content = """# PRIVACY POLICY

**Last Updated:** 23/10/2026

POLA respects your privacy and is committed to protecting your personal information.

## 1. Information We Collect

We may collect:

- Name
- Email address
- Phone number
- Profile information
- Payment transaction information
- Device information
- Precise location information (GPS coordinates) when you grant location permission
- Approximate location derived from your IP address
- Usage analytics
- Communications conducted through the Platform

## 2. How We Use Information

We use information to:

- Create and manage accounts.
- Deliver services and consultations.
- Provide location-based features, such as finding nearby lawyers and legal professionals.
- Process payments.
- Improve the Platform.
- Respond to user requests.
- Secure accounts and detect unusual device activity.
- Prevent fraud and abuse.
- Comply with legal obligations.

## 3. Location Data

With your permission, the App collects your device's precise GPS location.

We use location data to:

- Show you nearby lawyers and legal professionals, including distances and directions.
- Keep your device's recorded location up to date so location-based features work correctly. The App periodically sends your location to our servers while you are signed in.
- Help secure your account by detecting sign-ins and devices from unusual locations.

We also derive an approximate location from your IP address for security and analytics purposes.

You can disable location access at any time in your device settings. Features that depend on location, such as Nearby Lawyers, may not work without it. You may request deletion of your location data through our support channels or by deleting your account.

## 4. AI Processing

Information submitted to AI-powered features may be processed to generate responses and improve service quality.

Users should avoid submitting sensitive personal information unless necessary.

## 5. Payment Information

Payment transactions are processed by third-party payment providers.

POLA does not store complete payment card information on its servers.

## 6. Information Sharing

We do not sell personal information.

We may share information with:

- Payment providers.
- Service providers supporting platform operations.
- Professional consultants when necessary to provide requested services.
- Government authorities where required by law.

## 7. Data Security

We implement reasonable technical and organizational safeguards to protect user information.

No method of transmission or storage is completely secure, and absolute security cannot be guaranteed.

## 8. User Rights

Users may:

- Access their personal information.
- Request correction of inaccurate information.
- Request deletion of their account.
- Withdraw consent where applicable.

Requests may be submitted through our support channels.

## 9. Data Retention

Information is retained only as long as necessary for operational, legal, and security purposes.

## 10. Children's Privacy

The Platform is not intended for children under 18 years of age.

We do not knowingly collect personal information from children under 18.

## 11. Changes to This Policy

We may update this Privacy Policy periodically.

Updated versions will be posted within the Platform.

## 12. Contact

**Email:** polatanzania@gmail.com
**Company:** Olidox Company Limited
**Country:** Tanzania
"""

        privacy_content_sw = """# SERA YA FARAGHA

**Imesasishwa:** 23/10/2026

POLA inaheshimu faragha yako na inajitolea kulinda taarifa zako binafsi.

## 1. Taarifa Tunazokusanya

Tunaweza kukusanya:

- Jina
- Anwani ya barua pepe
- Nambari ya simu
- Maelezo ya wasifu
- Maelezo ya muamala wa malipo
- Maelezo ya kifaa
- Taarifa sahihi za mahali ulipo (vipimo vya GPS) unapotoa ruhusa ya mahali
- Makadirio ya mahali yanayotokana na anwani yako ya IP
- Uchambuzi wa matumizi
- Mawasiliano yaliyofanywa kupitia Jukwaa

## 2. Jinsi Tunavyotumia Taarifa

Tunatumia taarifa ili:

- Kuunda na kusimamia akaunti.
- Kutoa huduma na ushauri.
- Kutoa huduma zinazotegemea mahali, kama kupata mawakili na wataalamu walio karibu nawe.
- Kuchakata malipo.
- Kuboresha Jukwaa.
- Kujibu maombi ya watumiaji.
- Kulinda akaunti na kugundua shughuli za vifaa zisizo za kawaida.
- Kuzuia ulaghai na matumizi mabaya.
- Kufuata wajibu wa kisheria.

## 3. Data za Mahali Ulipo

Kwa idhini yako, Programu hukusanya mahali sahihi pa kifaa chako (GPS).

Tunatumia data za mahali ili:

- Kukuonyesha mawakili na wataalamu walio karibu nawe, ikijumuisha umbali na maelekezo.
- Kusasisha mahali pa kifaa chako ili huduma zinazotegemea mahali zifanye kazi vizuri. Programu hutuma mahali pako kwa seva zetu mara kwa mara wakati umeingia akaunti yako.
- Kusaidia kulinda akaunti yako kwa kugundua kuingia na vifaa kutoka maeneo yasiyo ya kawaida.

Tunapata pia makadirio ya mahali yanayotokana na anwani yako ya IP kwa madhumuni ya usalama na uchambuzi.

Unaweza kuzima ufikiaji wa mahali wakati wowote kwenye mipangilio ya kifaa chako. Huduma zinazotegemea mahali, kama Mawakili wa Karibu, zinaweza kutofanya kazi bila ruhusa hiyo. Unaweza kuomba kufutwa kwa data zako za mahali kupitia njia zetu za msaada au kwa kufuta akaunti yako.

## 4. Usindikaji wa AI

Taarifa zilizowasilishwa kwa huduma zinazotumia AI zinaweza kusindikwa ili kuzalisha majibu na kuboresha ubora wa huduma.

Watumiaji wanapaswa kuepuka kuwasilisha taarifa za kibinafsi zenye hisia isipokuwa ni lazima.

## 5. Maelezo ya Malipo

Muamala wa malipo huchakatwa na watoa huduma wa tatu wa malipo.

POLA hauhifadhi maelezo kamili ya kadi ya malipo kwenye seva zake.

## 6. Kushiriki Taarifa

Hatuuza taarifa za kibinafsi.

Tunaweza kushiriki taarifa na:

- Watoa huduma wa malipo.
- Watoa huduma wanaounga mkono uendeshaji wa jukwaa.
- Wataalamu wa kitaalamu wakati inahitajika kutoa huduma zilizoombwa.
- Mamlaka za serikali ambapo inahitajika na sheria.

## 7. Usalama wa Data

Tunatekeleza ulindaji wa kiufuni na wa kiutawala unaofaa kulinda taarifa za watumiaji.

Hakuna njia ya uwasilishaji au uhifadhi ambayo ni salama kabisa, na usalama wa kikamiliko hauwezi kuhakikishiwa.

## 8. Haki za Mtumiaji

Watumiaji wanaweza:

- Kufikia taarifa zao binafsi.
- Kuomba marekebisho ya taarifa zisizo sahihi.
- Kuomba kufutwa kwa akaunti yao.
- Kujiondoa idhini pale inapokubalika.

Ombi zinaweza kuwasilishwa kupitia mitandao yetu ya msaada.

## 9. Uhifadhi wa Data

Taarifa huhifadhiwa kwa muda unaohitajika tu kwa madhumuni ya uendeshaji, kisheria, na usalama.

## 10. Faragha ya Watoto

Jukwaa halijengewa watoto chini ya miaka 18.

Hatujui kusanya taarifa za kibinafsi kutoka kwa watoto chini ya miaka 18.

## 11. Mabadiliko ya Sera Hii

Tunaweza kusasisha Sera hii ya Faragha mara kwa mara.

Toleo zilizosasishwa zitawekwa ndani ya Jukwaa.

## 12. Mawasiliano

**Barua pepe:** polatanzania@gmail.com
**Kampuni:** Olidox Company Limited
**Nchi:** Tanzania
"""

        doc, created = DocumentContent.objects.update_or_create(
            slug='privacy-policy',
            defaults={
                'title': 'Privacy Policy',
                'title_sw': 'Sera ya Faragha',
                'category': 'privacy',
                'content': privacy_content,
                'content_sw': privacy_content_sw,
                'is_active': True,
                'is_public': True,
                'display_order': 3
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created: {doc.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'↻ Updated: {doc.title}'))

        self.stdout.write(self.style.SUCCESS('🎉 Document content seeding completed!'))
