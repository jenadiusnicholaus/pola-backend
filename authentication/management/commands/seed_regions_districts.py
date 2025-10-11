from django.core.management.base import BaseCommand
from authentication.models import Region, District

class Command(BaseCommand):
    help = 'Seed regions and districts data for Tanzania'

    def handle(self, *args, **kwargs):
        # Tanzania regions and districts data
        regions_data = {
            "Arusha": ["Arusha City", "Arusha", "Meru", "Karatu", "Longido", "Monduli", "Ngorongoro"],
            "Dar es Salaam": ["Ilala", "Kinondoni", "Temeke", "Ubungo", "Kigamboni"],
            "Dodoma": ["Dodoma City", "Bahi", "Chamwino", "Chemba", "Kondoa", "Kongwa", "Mpwapwa"],
            "Geita": ["Bukombe", "Chato", "Geita", "Mbogwe", "Nyang'hwale"],
            "Iringa": ["Iringa City", "Iringa", "Kilolo", "Mafinga Town", "Mufindi"],
            "Kagera": ["Biharamulo", "Bukoba District", "Bukoba City", "Karagwe", "Kyerwa", "Misenyi", "Ngara"],
            "Katavi": ["Mlele", "Mpanda District", "Mpanda Town"],
            "Kigoma": ["Buhigwe", "Kakonko", "Kasulu District", "Kasulu Town", "Kibondo", "Kigoma District", "Kigoma-Ujiji City", "Uvinza"],
            "Kilimanjaro": ["Hai", "Moshi District", "Moshi City", "Mwanga", "Rombo", "Same", "Siha"],
            "Lindi": ["Kilwa", "Lindi District", "Lindi City", "Liwale", "Nachingwea", "Ruangwa"],
            "Manyara": ["Babati District", "Babati Town", "Hanang", "Kiteto", "Mbulu", "Simanjiro"],
            "Mara": ["Bunda", "Butiama", "Musoma District", "Musoma City", "Rorya", "Serengeti", "Tarime"],
            "Mbeya": ["Chunya", "Kyela", "Mbarali", "Mbeya City", "Mbeya District", "Rungwe"],
            "Morogoro": ["Gairo", "Ifakara Town", "Kilombero", "Kilosa", "Malinyi", "Morogoro District", "Morogoro City", "Mvomero", "Ulanga"],
            "Mtwara": ["Masasi District", "Masasi Town", "Mtwara District", "Mtwara City", "Nanyumbu", "Newala", "Tandahimba"],
            "Mwanza": ["Ilemela City", "Kwimba", "Magu", "Misungwi", "Nyamagana City", "Sengerema", "Ukerewe"],
            "Njombe": ["Ludewa", "Makambako Town", "Makete", "Njombe District", "Njombe Town", "Wanging'ombe"],
            "Pwani": ["Bagamoyo", "Kibaha District", "Kibaha Town", "Kisarawe", "Mafia", "Mkuranga", "Rufiji"],
            "Rukwa": ["Kalambo", "Nkasi", "Sumbawanga District", "Sumbawanga City"],
            "Ruvuma": ["Mbinga", "Nyasa", "Songea District", "Songea City", "Tunduru"],
            "Shinyanga": ["Kahama Town", "Kahama District", "Kishapu", "Shinyanga District", "Shinyanga City"],
            "Simiyu": ["Bariadi District", "Bariadi Town", "Busega", "Itilima", "Maswa", "Meatu"],
            "Singida": ["Ikungi", "Iramba", "Manyoni", "Mkalama", "Singida District", "Singida City"],
            "Songwe": ["Ileje", "Mbozi", "Momba", "Songwe"],
            "Tabora": ["Igunga", "Kaliua", "Nzega", "Sikonge", "Tabora City", "Urambo", "Uyui"],
            "Tanga": ["Handeni District", "Handeni Town", "Kilindi", "Korogwe District", "Korogwe Town", "Lushoto", "Muheza", "Mkinga", "Pangani", "Tanga City"],
            "Zanzibar North": ["Kaskazini A", "Kaskazini B"],
            "Zanzibar South & Central": ["Kati", "Kusini"],
            "Zanzibar Urban/West": ["Magharibi A", "Magharibi B", "Mjini"],
            "Pemba North": ["Micheweni", "Wete"],
            "Pemba South": ["Chake Chake", "Mkoani"]
        }

        # Create regions and districts
        for region_name, districts in regions_data.items():
            self.stdout.write(f"Creating region: {region_name}")
            region, _ = Region.objects.get_or_create(name=region_name)
            
            for district_name in districts:
                self.stdout.write(f"Creating district: {district_name} in {region_name}")
                District.objects.get_or_create(
                    name=district_name,
                    region=region
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded regions and districts data'))
