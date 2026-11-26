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

**Last Updated:** 26/11/2026

This Privacy Policy explains how the POLA mobile application and platform ("POLA", "the App", "we") access, collect, use, share and protect your information. POLA is operated by Olidox Company Limited, Tanzania.

## 1. Information We Collect

**Information you provide:**

- Name, email address and phone number
- Profile information (such as profession, region, specializations and profile photo)
- Identity and professional verification documents you upload (such as ID cards and practising certificates)
- Questions, posts, comments and messages you send through the Platform
- Payment transaction information (such as transaction references and amounts)

**Information collected automatically:**

- Device information: device model, manufacturer, operating system and version, and a random device identifier generated by the App
- Push notification token, used to deliver notifications and incoming calls
- IP address, and an approximate location (country and city) derived from it
- Precise device location (GPS), only with your permission and only as described in Section 3
- App usage information collected through Google Firebase Analytics, including the Android advertising ID

We do **not** collect your IMEI, SIM serial number, phone number from your SIM, or other persistent hardware identifiers.

## 2. How We Use Information

We use information to:

- Create, verify and manage accounts.
- Deliver services, consultations, calls and messaging.
- Show lawyers and legal services near you.
- Process payments.
- Send notifications you have enabled.
- Secure accounts, including detecting sign-ins from new countries or unusual devices.
- Prevent fraud and abuse.
- Improve the Platform.
- Comply with legal obligations.

## 3. Location Data

Before the App requests location permission, it shows an in-app notice explaining how location is used. Location is only accessed if you tap "Allow" and grant the Android permission.

POLA collects your device's precise location only **while you are using the App**:

- **Nearby Lawyers:** when you open Nearby Lawyers or tap to use your current location, to show lawyers and legal services near you, with distances and directions.
- **Device registration:** when you sign in, your location is saved with your device registration and linked to your account.

POLA **never** collects location in the background or when the App is closed.

Your location is sent to our servers over an encrypted connection and linked to your account. Security checks use the approximate location derived from your IP address, not your GPS location.

You can decline location access and still use the App; you can choose a location on the map instead. You can withdraw permission at any time in your device settings.

## 4. Device Permissions

The App asks for permissions only when the related feature is used:

- **Location:** see Section 3.
- **Camera:** to take photos of verification documents or your profile picture.
- **Photos and files:** selected by you through the system picker, to upload documents and images.
- **Microphone:** for voice calls with professionals.
- **Notifications:** to alert you about messages, calls, bookings and updates.

## 5. AI Processing

Information submitted to AI-powered features may be processed to generate responses and improve service quality.

Users should avoid submitting sensitive personal information unless necessary.

## 6. Payment Information

Payments are processed by our payment provider (AzamPay) through mobile money and bank channels.

POLA does not store complete payment card or mobile money credentials on its servers.

## 7. Information Sharing

We do **not** sell personal information.

We share information only as needed to operate the Platform:

- **Google Firebase:** sign-in, push notifications and analytics.
- **Nexacon:** delivery of voice calls and in-app messages.
- **AzamPay:** payment processing.
- **Professionals you consult:** the information needed to provide the service you request.
- **Other users:** information you choose to make public, such as your profile, posts and comments.
- **Authorities:** where required by law or a valid legal request.

## 8. Data Security

All data sent between the App and our servers is encrypted in transit using HTTPS (TLS).

We apply access controls and other reasonable technical and organizational safeguards to protect your information. No method of transmission or storage is completely secure, and absolute security cannot be guaranteed.

## 9. Your Rights

You may:

- Access and update your personal information in the App.
- Request correction of inaccurate information.
- Delete specific data, or delete your account (see Section 10).
- Withdraw consent, including location permission, at any time.

## 10. Data Retention and Account Deletion

We keep your information while your account is active and as needed to provide the Platform.

**Deleting your account:**

- **In the App:** Settings > Delete Account.
- **On the web:** https://api.pola.co.tz/api/v1/authentication/deletion/account/
- **By email:** polatanzania@gmail.com

When you request deletion, your account is deactivated immediately. You can cancel by signing in within **30 days**. After 30 days, your account and associated personal data, including location data, are permanently deleted.

You can also delete specific data without closing your account in Settings > Manage My Data.

We may keep limited records after deletion where required by law, such as payment transaction records, and only for as long as legally required.

## 11. Children's Privacy

The Platform is not intended for children under 18 years of age.

We do not knowingly collect personal information from children under 18.

## 12. Changes to This Policy

We may update this Privacy Policy periodically. Updated versions will be posted within the Platform with a new "Last Updated" date.

## 13. Contact

For privacy questions or requests:

**Email:** polatanzania@gmail.com
**Company:** Olidox Company Limited
**Country:** Tanzania
"""

        privacy_content_sw = """# SERA YA FARAGHA

**Imesasishwa:** 26/11/2026

Sera hii ya Faragha inaeleza jinsi programu ya simu na jukwaa la POLA ("POLA", "Programu", "sisi") linavyofikia, kukusanya, kutumia, kushiriki na kulinda taarifa zako. POLA inaendeshwa na Olidox Company Limited, Tanzania.

## 1. Taarifa Tunazokusanya

**Taarifa unazotoa:**

- Jina, anwani ya barua pepe na nambari ya simu
- Maelezo ya wasifu (kama taaluma, mkoa, utaalamu na picha ya wasifu)
- Nyaraka za uthibitisho wa utambulisho na taaluma unazopakia (kama vitambulisho na vyeti vya kazi)
- Maswali, machapisho, maoni na ujumbe unaotuma kupitia Jukwaa
- Maelezo ya miamala ya malipo (kama namba za kumbukumbu na kiasi)

**Taarifa zinazokusanywa kiotomatiki:**

- Maelezo ya kifaa: modeli, mtengenezaji, mfumo wa uendeshaji na toleo lake, na kitambulisho cha kifaa cha nasibu kinachotengenezwa na Programu
- Tokeni ya arifa, inayotumika kuwasilisha arifa na simu zinazoingia
- Anwani ya IP, na makadirio ya mahali (nchi na mji) yanayotokana nayo
- Mahali sahihi pa kifaa (GPS), kwa idhini yako tu na kama ilivyoelezwa katika Sehemu ya 3
- Taarifa za matumizi ya Programu zinazokusanywa kupitia Google Firebase Analytics, ikijumuisha kitambulisho cha matangazo cha Android

**Hatukusanyi** IMEI, namba ya SIM, nambari ya simu kutoka kwenye SIM yako, au vitambulisho vingine vya kudumu vya kifaa.

## 2. Jinsi Tunavyotumia Taarifa

Tunatumia taarifa ili:

- Kuunda, kuthibitisha na kusimamia akaunti.
- Kutoa huduma, ushauri, simu na ujumbe.
- Kukuonyesha mawakili na huduma za kisheria zilizo karibu nawe.
- Kuchakata malipo.
- Kutuma arifa ulizoruhusu.
- Kulinda akaunti, ikijumuisha kugundua kuingia kutoka nchi mpya au vifaa visivyo vya kawaida.
- Kuzuia ulaghai na matumizi mabaya.
- Kuboresha Jukwaa.
- Kufuata wajibu wa kisheria.

## 3. Data za Mahali Ulipo

Kabla Programu haijaomba ruhusa ya mahali, inaonyesha taarifa ndani ya Programu inayoeleza jinsi mahali panavyotumika. Mahali hufikiwa tu ukibonyeza "Ruhusu" na kutoa ruhusa ya Android.

POLA hukusanya mahali sahihi pa kifaa chako **wakati unatumia Programu tu**:

- **Mawakili wa Karibu:** unapofungua Mawakili wa Karibu au kubonyeza kutumia mahali ulipo sasa, ili kukuonyesha mawakili na huduma za kisheria zilizo karibu nawe, pamoja na umbali na maelekezo.
- **Usajili wa kifaa:** unapoingia, mahali ulipo huhifadhiwa pamoja na usajili wa kifaa chako na kuunganishwa na akaunti yako.

POLA **kamwe** haikusanyi mahali chinichini au wakati Programu imefungwa.

Mahali ulipo hutumwa kwenye seva zetu kupitia muunganisho uliosimbwa na huunganishwa na akaunti yako. Ukaguzi wa usalama hutumia makadirio ya mahali yanayotokana na anwani yako ya IP, si mahali pako pa GPS.

Unaweza kukataa ufikiaji wa mahali na bado ukatumia Programu; unaweza kuchagua mahali kwenye ramani badala yake. Unaweza kuondoa ruhusa wakati wowote kwenye mipangilio ya kifaa chako.

## 4. Ruhusa za Kifaa

Programu huomba ruhusa tu wakati huduma husika inatumika:

- **Mahali:** tazama Sehemu ya 3.
- **Kamera:** kupiga picha za nyaraka za uthibitisho au picha yako ya wasifu.
- **Picha na faili:** unazochagua mwenyewe kupitia kichaguzi cha mfumo, ili kupakia nyaraka na picha.
- **Maikrofoni:** kwa simu za sauti na wataalamu.
- **Arifa:** kukujulisha kuhusu ujumbe, simu, miadi na masasisho.

## 5. Usindikaji wa AI

Taarifa zilizowasilishwa kwa huduma zinazotumia AI zinaweza kusindikwa ili kuzalisha majibu na kuboresha ubora wa huduma.

Watumiaji wanapaswa kuepuka kuwasilisha taarifa nyeti za kibinafsi isipokuwa ni lazima.

## 6. Maelezo ya Malipo

Malipo huchakatwa na mtoa huduma wetu wa malipo (AzamPay) kupitia pesa za simu na njia za benki.

POLA haihifadhi taarifa kamili za kadi ya malipo au za pesa za simu kwenye seva zake.

## 7. Kushiriki Taarifa

**Hatuuzi** taarifa za kibinafsi.

Tunashiriki taarifa pale tu inapohitajika kuendesha Jukwaa:

- **Google Firebase:** kuingia, arifa na uchambuzi.
- **Nexacon:** kuwasilisha simu za sauti na ujumbe ndani ya Programu.
- **AzamPay:** kuchakata malipo.
- **Wataalamu unaowashauri:** taarifa zinazohitajika kutoa huduma unayoomba.
- **Watumiaji wengine:** taarifa unazochagua kuweka hadharani, kama wasifu, machapisho na maoni yako.
- **Mamlaka:** pale inapohitajika na sheria au ombi halali la kisheria.

## 8. Usalama wa Data

Data zote zinazotumwa kati ya Programu na seva zetu husimbwa wakati wa kusafirishwa kwa kutumia HTTPS (TLS).

Tunatumia udhibiti wa ufikiaji na kinga nyingine za kiufundi na kiutawala zinazofaa kulinda taarifa zako. Hakuna njia ya uwasilishaji au uhifadhi iliyo salama kabisa, na usalama kamili hauwezi kuhakikishwa.

## 9. Haki Zako

Unaweza:

- Kufikia na kusasisha taarifa zako binafsi ndani ya Programu.
- Kuomba marekebisho ya taarifa zisizo sahihi.
- Kufuta data mahususi, au kufuta akaunti yako (tazama Sehemu ya 10).
- Kuondoa idhini, ikijumuisha ruhusa ya mahali, wakati wowote.

## 10. Uhifadhi wa Data na Kufuta Akaunti

Tunahifadhi taarifa zako wakati akaunti yako iko hai na kadri inavyohitajika kutoa Jukwaa.

**Kufuta akaunti yako:**

- **Ndani ya Programu:** Mipangilio > Futa Akaunti.
- **Kwenye wavuti:** https://api.pola.co.tz/api/v1/authentication/deletion/account/
- **Kwa barua pepe:** polatanzania@gmail.com

Unapoomba kufutwa, akaunti yako husimamishwa mara moja. Unaweza kughairi kwa kuingia ndani ya **siku 30**. Baada ya siku 30, akaunti yako na data binafsi zinazohusiana nayo, ikijumuisha data za mahali, hufutwa kabisa.

Unaweza pia kufuta data mahususi bila kufunga akaunti yako kupitia Mipangilio > Simamia Data Yangu.

Tunaweza kuhifadhi kumbukumbu chache baada ya kufuta pale inapohitajika na sheria, kama kumbukumbu za miamala ya malipo, na kwa muda unaohitajika kisheria tu.

## 11. Faragha ya Watoto

Jukwaa halikusudiwi kwa watoto walio chini ya miaka 18.

Hatukusanyi kwa makusudi taarifa za kibinafsi kutoka kwa watoto walio chini ya miaka 18.

## 12. Mabadiliko ya Sera Hii

Tunaweza kusasisha Sera hii ya Faragha mara kwa mara. Matoleo yaliyosasishwa yatawekwa ndani ya Jukwaa pamoja na tarehe mpya ya "Imesasishwa".

## 13. Mawasiliano

Kwa maswali au maombi kuhusu faragha:

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
