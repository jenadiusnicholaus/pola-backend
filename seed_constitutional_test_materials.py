#!/usr/bin/env python
"""
Seed Constitutional Law materials for testing PDF and rich text viewers in Flutter
"""
import os
import django
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from documents.models import LearningMaterial
from hubs.models import LegalEdTopic, LegalEdSubTopic
from authentication.models import PolaUser

def create_sample_pdf():
    """Create a sample PDF file for testing"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Constitutional Law - Fundamental Rights")
    
    # Content
    p.setFont("Helvetica", 12)
    y_position = height - 100
    
    content = [
        "1. INTRODUCTION TO FUNDAMENTAL RIGHTS",
        "",
        "Fundamental rights are basic human rights that are protected by the constitution.",
        "In Tanzania, these rights are enshrined in Chapter One of the Constitution.",
        "",
        "Key fundamental rights include:",
        "• Right to life and personal liberty",
        "• Freedom of expression and opinion", 
        "• Right to equality and non-discrimination",
        "• Right to fair trial and due process",
        "• Freedom of association and assembly",
        "",
        "2. ENFORCEMENT OF FUNDAMENTAL RIGHTS",
        "",
        "Citizens can seek enforcement of their fundamental rights through:",
        "- High Court proceedings under Basic Rights and Duties Enforcement Act",
        "- Constitutional petitions",
        "- Appeals to higher courts",
        "",
        "3. LIMITATIONS ON FUNDAMENTAL RIGHTS",
        "",
        "Rights may be limited in circumstances such as:",
        "- Public safety and order",
        "- National security considerations",
        "- Protection of rights of others",
        "- Morality and public health",
        "",
        "This document provides a comprehensive overview of constitutional rights",
        "and their practical application in Tanzanian law.",
    ]
    
    for line in content:
        if y_position < 50:  # Start new page if needed
            p.showPage()
            y_position = height - 50
        p.drawString(50, y_position, line)
        y_position -= 20
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def seed_constitutional_materials():
    """Seed Constitutional Law materials for testing"""
    print("🏛️ SEEDING CONSTITUTIONAL LAW TEST MATERIALS")
    print("=" * 50)
    
    # Get Constitutional Law topic
    try:
        topic = LegalEdTopic.objects.get(slug='constitutional-law')
        print(f"✅ Found topic: {topic.name}")
    except LegalEdTopic.DoesNotExist:
        print("❌ Constitutional Law topic not found")
        return
    
    # Get admin user for uploading
    try:
        # Try to find admin user by role first
        admin_user = PolaUser.objects.filter(user_role__role_name='admin').first()
        if not admin_user:
            # Fallback to superuser
            admin_user = PolaUser.objects.filter(is_superuser=True).first()
        if not admin_user:
            # Fallback to any user
            admin_user = PolaUser.objects.first()
        
        if admin_user:
            print(f"✅ Using user: {admin_user.email}")
        else:
            print("❌ No users found")
            return
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return
    
    # Create subtopic if needed
    subtopic, created = LegalEdSubTopic.objects.get_or_create(
        topic=topic,
        name="Fundamental Rights and Freedoms",
        defaults={
            'description': 'Basic constitutional rights and their enforcement mechanisms',
            'slug': 'fundamental-rights-freedoms'
        }
    )
    if created:
        print(f"✅ Created subtopic: {subtopic.name}")
    else:
        print(f"✅ Found subtopic: {subtopic.name}")
    
    print("\n📄 Creating materials...")
    
    # 1. PDF Material
    print("\n1️⃣ Creating PDF material...")
    try:
        # Check if PDF material already exists
        pdf_material, created = LearningMaterial.objects.get_or_create(
            title="Constitutional Rights - Complete Study Guide (PDF)",
            uploader=admin_user,
            subtopic=subtopic,
            defaults={
                'hub_type': 'legal_ed',
                'content_type': 'document',
                'uploader_type': 'admin',
                'description': 'Comprehensive PDF guide covering fundamental constitutional rights, enforcement mechanisms, and case studies. Perfect for in-depth study and reference.',
                'language': 'en',
                'price': 5000.00,  # Paid material
                'is_downloadable': True,
                'is_lecture_material': True,
                'is_verified_quality': True,
                'is_approved': True,
                'is_active': True
            }
        )
        
        if created or not pdf_material.file:
            # Create and attach PDF file
            pdf_content = create_sample_pdf()
            pdf_file = ContentFile(pdf_content, name='constitutional_rights_guide.pdf')
            pdf_material.file = pdf_file
            pdf_material.file_size = len(pdf_content)
            pdf_material.save()
            
            print(f"   ✅ Created PDF material: {pdf_material.title}")
            print(f"   📎 File: {pdf_material.file.name}")
            print(f"   💰 Price: {pdf_material.price} TZS")
        else:
            print(f"   ✅ PDF material already exists: {pdf_material.title}")
            
    except Exception as e:
        print(f"   ❌ Error creating PDF material: {e}")
    
    # 2. Rich Text Material
    print("\n2️⃣ Creating rich text material...")
    try:
        rich_text_content = """
        <div style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px;">
            <h1 style="color: #2c3e50; border-bottom: 2px solid #3498db;">🏛️ Constitutional Law Overview</h1>
            
            <h2 style="color: #34495e;">📖 Introduction</h2>
            <p>Constitutional law forms the foundation of Tanzania's legal system. It establishes the framework for government operations, defines the relationship between state institutions, and most importantly, protects the fundamental rights of citizens.</p>
            
            <div style="background-color: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #2980b9;">🔑 Key Constitutional Principles</h3>
                <ul>
                    <li><strong>Rule of Law:</strong> All persons and institutions are subject to law</li>
                    <li><strong>Separation of Powers:</strong> Executive, Legislative, and Judicial branches</li>
                    <li><strong>Protection of Rights:</strong> Fundamental rights and freedoms</li>
                    <li><strong>Democratic Governance:</strong> Participation and representation</li>
                </ul>
            </div>
            
            <h2 style="color: #34495e;">⚖️ Fundamental Rights Categories</h2>
            
            <div style="display: grid; gap: 15px;">
                <div style="border: 1px solid #bdc3c7; padding: 15px; border-radius: 5px;">
                    <h4 style="color: #e74c3c; margin-top: 0;">🛡️ Civil and Political Rights</h4>
                    <p>Rights that protect individual freedoms from government interference:</p>
                    <ul>
                        <li>Right to life and personal security</li>
                        <li>Freedom of expression and speech</li>
                        <li>Right to fair trial and due process</li>
                        <li>Freedom of movement and residence</li>
                    </ul>
                </div>
                
                <div style="border: 1px solid #bdc3c7; padding: 15px; border-radius: 5px;">
                    <h4 style="color: #f39c12; margin-top: 0;">🤝 Social and Economic Rights</h4>
                    <p>Rights that ensure basic human dignity and welfare:</p>
                    <ul>
                        <li>Right to education and healthcare</li>
                        <li>Right to work and fair wages</li>
                        <li>Right to adequate housing</li>
                        <li>Right to social security</li>
                    </ul>
                </div>
            </div>
            
            <h2 style="color: #34495e;">📋 Constitutional Review Process</h2>
            <p>The Tanzanian Constitution can be amended through a structured process:</p>
            
            <ol style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <li><strong>Proposal Stage:</strong> Amendment proposals must be initiated</li>
                <li><strong>Parliamentary Debate:</strong> Extensive discussion in Parliament</li>
                <li><strong>Public Participation:</strong> Citizen consultation and feedback</li>
                <li><strong>Referendum:</strong> National vote on significant changes</li>
                <li><strong>Implementation:</strong> Official adoption and enforcement</li>
            </ol>
            
            <div style="background-color: #d5f4e6; border: 1px solid #27ae60; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h3 style="color: #27ae60; margin-top: 0;">✅ Study Tips</h3>
                <p><strong>For effective constitutional law study:</strong></p>
                <ul>
                    <li>📚 Read landmark constitutional cases</li>
                    <li>🔍 Analyze comparative constitutional systems</li>
                    <li>💭 Understand the historical context of provisions</li>
                    <li>⚖️ Practice constitutional interpretation methods</li>
                    <li>📖 Stay updated on constitutional developments</li>
                </ul>
            </div>
            
            <h2 style="color: #34495e;">📚 Further Reading</h2>
            <p>For comprehensive understanding, students should explore:</p>
            <ul>
                <li>Constitution of the United Republic of Tanzania (1977)</li>
                <li>Basic Rights and Duties Enforcement Act</li>
                <li>Leading constitutional law cases</li>
                <li>Comparative constitutional analysis</li>
            </ul>
            
            <hr style="margin: 30px 0; border: none; border-top: 2px solid #ecf0f1;">
            <p style="text-align: center; color: #7f8c8d; font-style: italic;">
                This content is designed for educational purposes and provides a foundational understanding of constitutional law principles in Tanzania.
            </p>
        </div>
        """
        
        rich_material, created = LearningMaterial.objects.get_or_create(
            title="Constitutional Law Fundamentals - Interactive Guide",
            uploader=admin_user,
            subtopic=subtopic,
            defaults={
                'hub_type': 'legal_ed',
                'content_type': 'article',
                'uploader_type': 'admin',
                'description': 'Interactive rich-text guide covering constitutional law basics with visual elements, examples, and study tips. Perfect for quick learning and review.',
                'content': rich_text_content,
                'language': 'en',
                'price': 0.00,  # Free material
                'is_downloadable': False,  # Rich text - no download needed
                'is_lecture_material': True,
                'is_verified_quality': True,
                'is_approved': True,
                'is_active': True
            }
        )
        
        if created:
            print(f"   ✅ Created rich text material: {rich_material.title}")
            print(f"   📝 Content type: {rich_material.content_type}")
            print(f"   💰 Price: {rich_material.price} TZS (FREE)")
        else:
            print(f"   ✅ Rich text material already exists: {rich_material.title}")
            
    except Exception as e:
        print(f"   ❌ Error creating rich text material: {e}")
    
    print("\n📊 SEEDING COMPLETE!")
    print("=" * 50)
    
    # Summary
    materials = LearningMaterial.objects.filter(subtopic=subtopic)
    print(f"📈 Total materials in '{subtopic.name}': {materials.count()}")
    
    for material in materials:
        viewer_type = "PDF Viewer" if material.file else "Document Reader"
        content_indicator = "📄 PDF File" if material.file else "📝 Rich Text"
        price_indicator = "💰 Paid" if material.price > 0 else "🆓 Free"
        
        print(f"  • {material.title}")
        print(f"    {content_indicator} | {viewer_type} | {price_indicator}")
    
    print(f"\n🎯 Test Materials Ready!")
    print(f"Flutter can now test:")
    print(f"  1. PDF viewer with the PDF material")
    print(f"  2. Rich text document reader with the HTML content material")

if __name__ == "__main__":
    try:
        seed_constitutional_materials()
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()