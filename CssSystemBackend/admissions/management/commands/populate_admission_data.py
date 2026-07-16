from django.core.management.base import BaseCommand
from admissions.models import AdmissionCriteria, AdmissionGuideline, FAQ, ImportantDate, SubjectGradeMapping
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Populate sample KNUST admission data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating sample admission data...')
        
        # Create WASSCE grade mappings (CRITICAL: Must be created first!)
        self.stdout.write('Creating WASSCE grade mappings...')
        grade_mappings = [
            {'grade': 'A1', 'numerical_value': 1, 'description': 'Excellent'},
            {'grade': 'B2', 'numerical_value': 2, 'description': 'Very Good'},
            {'grade': 'B3', 'numerical_value': 3, 'description': 'Good'},
            {'grade': 'C4', 'numerical_value': 4, 'description': 'Credit'},
            {'grade': 'C5', 'numerical_value': 5, 'description': 'Credit'},
            {'grade': 'C6', 'numerical_value': 6, 'description': 'Credit'},
            {'grade': 'D7', 'numerical_value': 7, 'description': 'Pass'},
            {'grade': 'E8', 'numerical_value': 8, 'description': 'Pass'},
            {'grade': 'F9', 'numerical_value': 9, 'description': 'Fail'},
        ]
        
        for mapping in grade_mappings:
            SubjectGradeMapping.objects.get_or_create(
                grade=mapping['grade'],
                defaults={
                    'numerical_value': mapping['numerical_value'],
                    'description': mapping['description']
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(grade_mappings)} grade mappings'))
        
        # Create admission criteria for CS and IT based on KNUST official requirements
        # Cut-off aggregates from 2024/2025: CS = 07, IT = 10
        cs_criteria, created = AdmissionCriteria.objects.get_or_create(
            program='CS',
            academic_year='2025/2026',
            defaults={
                'aggregate_cutoff': 7,  # Official 2024/2025 cut-off aggregate for CS
                'core_math_min_grade': 'C6',
                'english_min_grade': 'C6',
                'integrated_science_min_grade': 'C6',
                'social_studies_min_grade': 'C6',
                'elective_math_required': True,
                'elective_math_min_grade': 'C6',
                'physics_required': True,
                'physics_min_grade': 'C6',
                'science_electives_required': 3,  # Elective Math + Physics + (Chemistry OR Applied Electricity OR Electronics)
                'additional_requirements': 'Core Subjects: Credit passes (A1-C6) in English Language, Mathematics, and Integrated Science. Elective Subjects: Credit passes in Mathematics, Physics and either Chemistry or Applied Electricity or Electronics.',
                'is_active': True
            }
        )
        
        it_criteria, created = AdmissionCriteria.objects.get_or_create(
            program='IT',
            academic_year='2025/2026',
            defaults={
                'aggregate_cutoff': 10,  # Official 2024/2025 cut-off aggregate for IT
                'core_math_min_grade': 'C6',
                'english_min_grade': 'C6',
                'integrated_science_min_grade': 'C6',
                'social_studies_min_grade': 'C6',
                'elective_math_required': True,
                'elective_math_min_grade': 'C6',
                'physics_required': False,  # IT does not require Physics
                'physics_min_grade': 'C6',
                'science_electives_required': 3,  # Elective Math + any TWO subjects from various programmes
                'additional_requirements': 'Core Subjects: Credit passes (A1-C6) in English Language, Mathematics, and Integrated Science. Elective Subjects: Credit passes in Mathematics and any TWO (2) subjects from General Science, General Arts, Business, Visual Art, Technical, or Home Economics programmes.',
                'is_active': True
            }
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Created admission criteria'))
        
        # Create admission guidelines based on official KNUST requirements
        guidelines = [
            {
                'title': 'How to Purchase KNUST E-Voucher',
                'guide_type': 'VOUCHER',
                'order': 1,
                'content': '''STEP 1: PURCHASE OF E-VOUCHER

All applicants (Ghanaian and International) must obtain an E-Voucher. There are three options:

Option 1: Online Purchase (All Applicants)
1. Visit https://apps.knust.edu.gh/admissions/
2. Register with a valid email address
3. Login and purchase voucher via Mastercard, Visa or Mobile Money
4. Proceed with application

Option 2: USSD Purchase (Ghanaian Applicants Only)
1. From mobile device, dial *415*55#
2. Follow prompts to purchase via Mobile Money
3. Visit https://apps.knust.edu.gh/admissions/
4. Register with valid email address
5. Login, validate voucher, and proceed with application

Option 3: Ghana Post (Ghanaian Applicants Only)
1. Purchase voucher from Regional or designated Ghana Post offices
2. Visit https://apps.knust.edu.gh/admissions/
3. Register with valid email address
4. Login, validate voucher, and proceed with application

International Applicants:
All international applicants must pay a non-refundable application processing fee of US$100.00''',
                'portal_url': 'https://apps.knust.edu.gh/admissions/',
                'is_active': True
            },
            {
                'title': 'Required Documents Checklist',
                'guide_type': 'DOCUMENTS',
                'order': 2,
                'content': '''REQUIRED DOCUMENTS FOR ALL APPLICANTS:

1. Examination Results (One of the following):
   • WASSCE/SSSCE
   • GCE/IGCSE (Cambridge) O & A Level
   • GBCE and ABCE
   • International Baccalaureate (IB)
   • American High School Grade 12
   • HND Certificate plus High School Results
   • Other International High School Results

2. Birth Certificate (Original or certified copy)

3. Ghana Card/Passport

4. Passport Photograph (Light green background)

5. For Non-English Speaking Countries:
   • Minimum one-year English Proficiency Certificate

Document Format for Upload:
• PDF format
• Maximum 2MB per document
• Clear and legible scans

Note: Documents not in English must be accompanied by accredited English translations.''',
                'portal_url': '',
                'is_active': True
            },
            {
                'title': 'How to Complete Your Application',
                'guide_type': 'APPLICATION',
                'order': 3,
                'content': '''STEP 2: APPLICATION PROCESS

1. Login to Portal:
   Visit https://apps.knust.edu.gh/admissions/apply/Account/Login
   Enter voucher credentials

2. Personal Information:
   • Complete all mandatory fields marked with *
   • Save and exit if needed to continue later
   • Save and proceed when ready

3. Educational Background:
   • If institution not listed, select "Private"

4. Examination Results:
   a) Examination Type: If not listed, select "Certification/Diploma/Degree"
   b) Sitting: Select May/June (School) if not WASSCE/SSSCE
   c) Year: Select examination year
   d) Index Number: Enter candidate/examination ID
   
5. Subjects and Grades:
   • Select all subjects offered in high school
   • Enter corresponding grades
   • If awaiting results, select "awaiting" as grade
   • Select "Add Results" if you have multiple certificates

6. Upload Documents (PDF format):
   • Birth Certificate
   • Results slips/Certificates (for non-WASSCE applicants)

7. Applicant Declaration:
   • Read and agree that all information is true
   • Tick to declare

8. Programme Choices:
   • Select "Regular" as Stream
   • Tick "Yes" if you want fee-paying/parallel consideration
   • Choose up to 3 programmes

9. Upload Identification:
   • Ghana Card/Passport (PDF format)

10. Review and Submit:
    • Check all information carefully
    • Tick final declaration
    • Submit application
    • Keep copy for personal reference

IMPORTANT NOTES:
• Don't leave application inactive for more than 5 minutes (auto logout)
• Application can be edited until deadline
• Check subject requirements before selecting programme
• International results may require GTEC evaluation''',
                'portal_url': 'https://apps.knust.edu.gh/admissions/apply/Account/Login',
                'is_active': True
            },
            {
                'title': 'Check Your Admission Status',
                'guide_type': 'STATUS',
                'order': 4,
                'content': '''HOW TO CHECK ADMISSION STATUS:

Visit: https://apps.knust.edu.gh/admissions/check/Home/Undergraduates
Enter your application number

Application Status Types:
• "Pending" - Application under review
• "Shortlisted" - You meet basic requirements
• "Admitted" - Congratulations! You're admitted
• "Not Admitted" - Not admitted this cycle
• "Awaiting Documents" - Additional documents needed

If Admitted:
1. Download admission letter
2. Print admission letter
3. Note registration deadline
4. Proceed to pay fees
5. Complete online registration

Important:
• Check status regularly during admission period
• Admission letters released in batches
• Follow KNUST social media for updates''',
                'portal_url': 'https://apps.knust.edu.gh/admissions/check/Home/Undergraduates',
                'is_active': True
            },
            {
                'title': 'BSc. Computer Science - Requirements',
                'guide_type': 'GENERAL',
                'order': 5,
                'content': '''BSc. COMPUTER SCIENCE (4 Years)

Programme Code: 203
2024/2025 Cut-off Aggregate: 07

A. WASSCE/SSSCE Requirements:
Core Subjects (Credit passes A1-C6):
• English Language
• Mathematics
• Integrated Science

Elective Subjects (Credit passes A1-C6):
• Mathematics (Elective)
• Physics
• Either Chemistry OR Applied Electricity OR Electronics

B. GCE/IGCSE 'A' & 'O' Levels:
• O' Level: Five (5) credits including English Language, Mathematics, and Additional/Elective Mathematics
• A' Level: Three (3) credits including Mathematics

C. Mature Applicants:
• Must be at least 25 years old
• Must satisfy general requirements (WASSCE/SSSCE or A Level or HND/Diploma)
• Shortlisted applicants take Entrance Examination and interview

Note: THREE Core Subjects are prerequisite for all KNUST programmes''',
                'portal_url': 'https://apps.knust.edu.gh/admissions/',
                'is_active': True
            },
            {
                'title': 'BSc. Information Technology - Requirements',
                'guide_type': 'GENERAL',
                'order': 6,
                'content': '''BSc. INFORMATION TECHNOLOGY (4 Years)

Programme Code: 1634
2024/2025 Cut-off Aggregate: 10

A. WASSCE/SSSCE Requirements:
Core Subjects (Credit passes A1-C6):
• English Language
• Mathematics
• Integrated Science

Elective Subjects (Credit passes A1-C6):
• Mathematics (Elective)
• Any TWO (2) subjects from:
  - General Science
  - General Arts
  - Business
  - Visual Art
  - Technical
  - Home Economics

B. GCE/IGCSE 'A' & 'O' Levels:
• O' Level: Five (5) credits including English Language, Mathematics, and Additional/Elective Mathematics
• A' Level: Three (3) credits including Mathematics

C. Mature Applicants:
• Must be at least 25 years old
• Must satisfy general requirements (WASSCE/SSSCE or A Level or HND/Diploma)
• Shortlisted applicants take Entrance Examination and interview

Note: Physics is NOT required for Information Technology''',
                'portal_url': 'https://apps.knust.edu.gh/admissions/',
                'is_active': True
            }
        ]
        
        for guide_data in guidelines:
            AdmissionGuideline.objects.get_or_create(
                title=guide_data['title'],
                defaults=guide_data
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Created admission guidelines'))
        
        # Create FAQs based on official KNUST requirements
        faqs = [
            {
                'question': 'What is the cut-off aggregate for Computer Science at KNUST?',
                'answer': 'The cut-off aggregate for BSc. Computer Science for 2024/2025 academic year is 07. This means you need an aggregate of 7 or better (lower is better in WASSCE grading). Note: Cut-off aggregates may vary year to year based on pass rate and available spaces.',
                'category': 'REQUIREMENTS',
                'order': 1
            },
            {
                'question': 'What is the cut-off aggregate for Information Technology at KNUST?',
                'answer': 'The cut-off aggregate for BSc. Information Technology for 2024/2025 academic year is 10. This means you need an aggregate of 10 or better. Cut-off aggregates vary yearly.',
                'category': 'REQUIREMENTS',
                'order': 2
            },
            {
                'question': 'What subjects are required for Computer Science?',
                'answer': 'Core Subjects: Credit passes (A1-C6) in English Language, Mathematics, and Integrated Science. Elective Subjects: Credit passes in Mathematics (Elective), Physics, and either Chemistry OR Applied Electricity OR Electronics.',
                'category': 'REQUIREMENTS',
                'order': 3
            },
            {
                'question': 'What subjects are required for Information Technology?',
                'answer': 'Core Subjects: Credit passes (A1-C6) in English Language, Mathematics, and Integrated Science. Elective Subjects: Credit passes in Mathematics (Elective) and any TWO subjects from General Science, General Arts, Business, Visual Art, Technical, or Home Economics programmes. Physics is NOT required for IT.',
                'category': 'REQUIREMENTS',
                'order': 4
            },
            {
                'question': 'How do I purchase an admission voucher?',
                'answer': 'Three options: 1) Online at https://apps.knust.edu.gh/admissions/ via Mastercard, Visa or Mobile Money. 2) Dial *415*55# from mobile device (Ghanaians only). 3) Purchase from Ghana Post regional offices (Ghanaians only). International applicants pay US$100 processing fee.',
                'category': 'APPLICATION',
                'order': 5
            },
            {
                'question': 'What documents do I need for application?',
                'answer': 'Required: Examination results (WASSCE/SSSCE or equivalent), Birth Certificate, Ghana Card/Passport, Passport photo (light green background). For non-English speakers: One-year English Proficiency Certificate. All documents in PDF format, max 2MB each.',
                'category': 'DOCUMENTS',
                'order': 6
            },
            {
                'question': 'Can I apply with awaiting results?',
                'answer': 'Yes, you can apply while awaiting results. Select "awaiting" as the grade for subjects with pending results. You must update with final grades before the deadline.',
                'category': 'APPLICATION',
                'order': 7
            },
            {
                'question': 'How many programmes can I select?',
                'answer': 'You can select up to 3 programmes with one voucher. Rank them in order of preference. Select "Regular" as stream and indicate if you want to be considered for fee-paying/parallel programmes.',
                'category': 'APPLICATION',
                'order': 8
            },
            {
                'question': 'How do I check my admission status?',
                'answer': 'Visit https://apps.knust.edu.gh/admissions/check/Home/Undergraduates and enter your application number. Admission letters are released in batches between January and February.',
                'category': 'APPLICATION',
                'order': 9
            },
            {
                'question': 'What is the difference between Computer Science and Information Technology?',
                'answer': 'Computer Science (aggregate 07) focuses on theoretical foundations, algorithms, and software development. Requires Physics. Information Technology (aggregate 10) emphasizes practical applications, systems administration, and IT management. Does NOT require Physics and accepts electives from various programmes.',
                'category': 'PROGRAMS',
                'order': 10
            },
            {
                'question': 'Can mature applicants apply?',
                'answer': 'Yes. Mature applicants must be at least 25 years old and satisfy general requirements (WASSCE/SSSCE, A Level, or HND/Diploma). Shortlisted applicants take an Entrance Examination and interview.',
                'category': 'REQUIREMENTS',
                'order': 11
            },
            {
                'question': 'What if my examination is not WASSCE?',
                'answer': 'KNUST accepts: GCE/IGCSE O & A Levels, GBCE/ABCE, International Baccalaureate (IB), American High School Grade 12, HND, and other international results. Some may require GTEC evaluation. Select your examination type during application or choose "Certification/Diploma/Degree" if not listed.',
                'category': 'REQUIREMENTS',
                'order': 12
            }
        ]
        
        for faq_data in faqs:
            FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Created FAQs'))
        
        # Create important dates
        today = date.today()
        dates = [
            {
                'event_type': 'APPLICATION_OPEN',
                'title': 'Application Portal Opens',
                'description': 'Online application portal opens for 2025/2026 admissions',
                'event_date': today + timedelta(days=30),
                'academic_year': '2025/2026'
            },
            {
                'event_type': 'APPLICATION_CLOSE',
                'title': 'Application Deadline',
                'description': 'Last day to submit applications for 2025/2026 academic year',
                'event_date': today + timedelta(days=120),
                'academic_year': '2025/2026'
            },
            {
                'event_type': 'RESULTS',
                'title': 'Admission Results Release',
                'description': 'First batch of admission letters to be released',
                'event_date': today + timedelta(days=180),
                'academic_year': '2025/2026'
            },
            {
                'event_type': 'ORIENTATION',
                'title': 'Freshers Orientation',
                'description': 'Orientation week for newly admitted students',
                'event_date': today + timedelta(days=240),
                'academic_year': '2025/2026'
            }
        ]
        
        for date_data in dates:
            ImportantDate.objects.get_or_create(
                title=date_data['title'],
                academic_year=date_data['academic_year'],
                defaults=date_data
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Created important dates'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Successfully populated all sample data!'))
        self.stdout.write(self.style.SUCCESS('\nYou can now:'))
        self.stdout.write('  1. Access admin panel to manage criteria')
        self.stdout.write('  2. Use API endpoints for eligibility checks')
        self.stdout.write('  3. Update guidelines and FAQs as needed')
