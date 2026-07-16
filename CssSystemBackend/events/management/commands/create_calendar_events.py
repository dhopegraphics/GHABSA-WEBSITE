from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, time
from events.models import Event
from django.db import transaction


class Command(BaseCommand):
    help = 'Create all CSS events for 2025-26 academic year from the events calendar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if events already exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating events',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating CSS Events Calendar 2025-26...'))

        # Define all events with their details
        events_data = [
            # FIRST SEMESTER (JANUARY - APRIL 2026)
            {
                'name': 'Info Session: "What to Expect on Campus"',
                'date': '2026-01-09',
                'time': '18:00',
                'type': 'seminar',
                'venue': 'NB LT1',
                'description': 'Welcome session for new students to understand campus life, academic expectations, and available resources. Learn about student services, academic support, and how to navigate your first semester successfully.',
                'emoji': '🎓',
                'organised_by': 'CSS Executive Committee'
            },
            {
                'name': 'Course Review / Photoshoot & Tour',
                'date': '2026-01-09',
                'time': '14:00',
                'type': 'social',
                'venue': 'CS Department',
                'description': 'Interactive course review session combined with campus photoshoot and guided tour of computer science facilities. Perfect opportunity to meet fellow students and familiarize yourself with the department.',
                'emoji': '📸',
                'organised_by': 'CSS Media Team'
            },
            {
                'name': 'Mindshift',
                'date': '2026-01-21',
                'time': '15:00',
                'type': 'talk',
                'venue': 'NB LT2',
                'description': 'Transformative session focused on developing the right mindset for academic and personal success. Learn about growth mindset, overcoming challenges, and building resilience in your tech journey.',
                'emoji': '🧠',
                'organised_by': 'CSS Mentorship Committee'
            },
            {
                'name': 'Tech Industry Symposium',
                'date': '2026-02-04',
                'time': '10:00',
                'type': 'conference',
                'venue': 'Great Hall',
                'description': 'Annual symposium bringing together industry leaders, alumni, and current students to discuss latest trends in technology, career opportunities, and industry insights. Features keynote speakers from top tech companies.',
                'emoji': '🚀',
                'organised_by': 'CSS Career Development'
            },
            {
                'name': 'Unplug and Play (Games & Socials)',
                'date': '2026-02-07',
                'time': '16:00',
                'type': 'social',
                'venue': 'CS Common Area',
                'description': 'Fun-filled afternoon of board games, video games, and social activities. Take a break from academics and connect with fellow students in a relaxed, entertaining environment.',
                'emoji': '🎮',
                'organised_by': 'CSS Entertainment Committee'
            },
            {
                'name': 'Val\'s Day Movie Night in Colab with Scisa',
                'date': '2026-02-14',
                'time': '19:00',
                'type': 'social',
                'venue': 'Auditorium',
                'description': 'Valentine\'s Day movie screening in collaboration with SCISA. Enjoy romantic comedies, snacks, and great company. Perfect date night or friends\' night out for the tech community.',
                'emoji': '❤️',
                'organised_by': 'CSS & SCISA'
            },
            {
                'name': 'Visual Rave with Septemba Degree',
                'date': '2026-02-18',
                'time': '20:00',
                'type': 'social',
                'venue': 'Unity Hall',
                'description': 'High-energy visual rave featuring live DJ performance by Septemba Degree. Experience cutting-edge visual effects, electronic music, and an unforgettable night of dancing and entertainment.',
                'emoji': '🎵',
                'organised_by': 'CSS Entertainment'
            },
            {
                'name': 'Fix It First',
                'date': '2026-02-21',
                'time': '14:00',
                'type': 'workshop',
                'venue': 'CS Lab 1',
                'description': 'Hands-on workshop focused on troubleshooting and fixing common technical problems. Learn debugging techniques, hardware troubleshooting, and problem-solving methodologies.',
                'emoji': '🔧',
                'organised_by': 'CSS Technical Team'
            },
            {
                'name': 'CSS Aerobic & Sports Day',
                'date': '2026-02-28',
                'time': '08:00',
                'type': 'social',
                'venue': 'Sports Complex',
                'description': 'Annual sports and fitness day featuring aerobic sessions, football, basketball, and various sports competitions. Promote health, wellness, and team spirit within the CSS community.',
                'emoji': '⚽',
                'organised_by': 'CSS Sports Committee'
            },
            {
                'name': 'WICS Week: Web3 & Blockchain "Zero to Dap"',
                'date': '2026-03-02',
                'end_date': '2026-03-06',
                'time': '15:00',
                'type': 'workshop',
                'venue': 'CS Labs',
                'description': 'Comprehensive 5-day workshop series on Web3 and Blockchain technology. Learn from zero to building your first decentralized application (DApp). Covers smart contracts, cryptocurrency, and blockchain fundamentals.',
                'emoji': '⛓️',
                'organised_by': 'Women in Computer Science (WICS)'
            },
            {
                'name': 'General Assembly',
                'date': '2026-03-04',
                'time': '17:00',
                'type': 'meeting',
                'venue': 'Great Hall',
                'description': 'Mid-semester general assembly to discuss CSS activities, budget updates, upcoming events, and address student concerns. All CSS members are encouraged to participate in decision-making.',
                'emoji': '📋',
                'organised_by': 'CSS Executive Committee'
            },
            {
                'name': 'Financial Literacy',
                'date': '2026-03-11',
                'time': '16:00',
                'type': 'seminar',
                'venue': 'NB LT1',
                'description': 'Essential financial literacy session covering personal finance, budgeting, investment basics, and financial planning for students. Learn money management skills for your academic and professional journey.',
                'emoji': '💰',
                'organised_by': 'CSS Financial Committee'
            },
            {
                'name': 'Emerging Tech with Teinc Solutions',
                'date': '2026-03-18',
                'time': '14:00',
                'type': 'talk',
                'venue': 'NB LT2',
                'description': 'Industry talk by Teinc Solutions on emerging technologies and their impact on the tech industry. Explore AI, IoT, machine learning, and future tech trends with industry experts.',
                'emoji': '🔬',
                'organised_by': 'CSS & Teinc Solutions'
            },
            {
                'name': 'Game Development Bootcamp',
                'date': '2026-03-25',
                'time': '10:00',
                'type': 'workshop',
                'venue': 'CS Lab 2',
                'description': 'Intensive bootcamp on game development covering game engines, programming concepts, graphics, and game design principles. Build your first game from concept to completion.',
                'emoji': '🎮',
                'organised_by': 'CSS Game Dev Club'
            },
            {
                'name': 'DigiNovate Event',
                'date': '2026-03-28',
                'time': '09:00',
                'type': 'conference',
                'venue': 'Innovation Hub',
                'description': 'Digital innovation conference showcasing student projects, startup pitches, and innovative tech solutions. Network with entrepreneurs, investors, and tech innovators.',
                'emoji': '💡',
                'organised_by': 'CSS Innovation Committee'
            },
            
            # SECOND SEMESTER (MAY - SEPTEMBER 2026)
            {
                'name': 'Edubridge with Greener Educational Consult',
                'date': '2026-05-27',
                'time': '15:00',
                'type': 'seminar',
                'venue': 'NB LT1',
                'description': 'Educational bridge session with Greener Educational Consult focusing on scholarship opportunities, study abroad programs, and educational pathways for computer science students.',
                'emoji': '🌍',
                'organised_by': 'CSS & Greener Educational Consult'
            },
            {
                'name': 'Behind the Lens',
                'date': '2026-06-03',
                'time': '16:00',
                'type': 'workshop',
                'venue': 'Media Studio',
                'description': 'Photography and videography workshop exploring the technical and creative aspects of digital media production. Learn camera techniques, editing, and visual storytelling.',
                'emoji': '📷',
                'organised_by': 'CSS Media Committee'
            },
            {
                'name': '2-Day Hackathon with Dr. Agyemang',
                'date': '2026-06-10',
                'end_date': '2026-06-11',
                'time': '09:00',
                'type': 'competition',
                'venue': 'CS Labs',
                'description': 'Intensive 2-day hackathon mentored by Dr. Agyemang. Teams compete to build innovative software solutions addressing real-world problems. Prizes awarded for best projects.',
                'emoji': '💻',
                'organised_by': 'CSS & Dr. Agyemang'
            },
            {
                'name': 'Kalykap 4.0',
                'date': '2026-06-13',
                'time': '18:00',
                'type': 'social',
                'venue': 'Unity Hall',
                'description': 'Fourth edition of the popular Kalykap social event. Evening of music, dance, networking, and entertainment celebrating the CSS community and African culture.',
                'emoji': '🎉',
                'organised_by': 'CSS Entertainment Committee'
            },
            {
                'name': 'Mobile Development Bootcamp',
                'date': '2026-06-24',
                'time': '10:00',
                'type': 'workshop',
                'venue': 'CS Lab 1',
                'description': 'Comprehensive mobile app development bootcamp covering iOS and Android development. Learn React Native, Flutter, and native app development from industry professionals.',
                'emoji': '📱',
                'organised_by': 'CSS Mobile Dev Team'
            },
            {
                'name': 'Prof. Acquah Byte Battle (TPABB) and Official Monday',
                'date': '2026-07-13',
                'time': '14:00',
                'type': 'competition',
                'venue': 'CS Department',
                'description': 'Annual programming competition honoring Prof. Acquah. Students compete in algorithmic challenges and coding problems. Combined with official department activities.',
                'emoji': '⚔️',
                'organised_by': 'CSS Academic Committee'
            },
            {
                'name': 'Jersey Day',
                'date': '2026-07-14',
                'time': '08:00',
                'type': 'social',
                'venue': 'Campus-wide',
                'description': 'Annual CSS jersey day where all members wear their CSS jerseys to show unity and pride. Special photo sessions and community building activities throughout the day.',
                'emoji': '👕',
                'organised_by': 'CSS Executive Committee'
            },
            {
                'name': 'Alumni Homecoming & Code Quest & "Tell Your Story" Event',
                'date': '2026-07-15',
                'time': '10:00',
                'type': 'conference',
                'venue': 'Great Hall',
                'description': 'Triple event featuring alumni homecoming, coding competition, and storytelling session. Alumni share their career journeys while current students compete in coding challenges.',
                'emoji': '🏆',
                'organised_by': 'CSS Alumni Relations'
            },
            {
                'name': 'Outreach Program',
                'date': '2026-07-16',
                'time': '09:00',
                'type': 'other',
                'venue': 'Various Schools',
                'description': 'Community outreach program visiting local schools to introduce students to computer science and technology. Promote STEM education and inspire the next generation.',
                'emoji': '🤝',
                'organised_by': 'CSS Community Service'
            },
            {
                'name': 'General Assembly and African Wear Day',
                'date': '2026-07-17',
                'time': '15:00',
                'type': 'meeting',
                'venue': 'Great Hall',
                'description': 'End-of-semester general assembly combined with African wear day celebration. Review semester achievements, elect new leaders, and celebrate African heritage and culture.',
                'emoji': '🌍',
                'organised_by': 'CSS Executive Committee'
            },
            {
                'name': 'Hob Nob',
                'date': '2026-07-18',
                'time': '19:00',
                'type': 'social',
                'venue': 'Unity Hall',
                'description': 'Elegant networking and social event bringing together students, faculty, and industry professionals. Formal dress code with dinner, networking, and entertainment.',
                'emoji': '🥂',
                'organised_by': 'CSS Social Committee'
            },
            {
                'name': 'Industry X Campus',
                'date': '2026-07-22',
                'time': '13:00',
                'type': 'conference',
                'venue': 'Innovation Hub',
                'description': 'Industry-academia collaboration event connecting students with tech companies. Features career fairs, company presentations, internship opportunities, and networking sessions.',
                'emoji': '🏢',
                'organised_by': 'CSS Career Services'
            },
            {
                'name': 'Code Fest',
                'date': '2026-07-24',
                'time': '09:00',
                'type': 'competition',
                'venue': 'CS Labs',
                'description': 'Final coding competition of the academic year featuring multiple programming challenges, algorithm contests, and project showcases. Celebration of coding excellence.',
                'emoji': '🏆',
                'organised_by': 'CSS Programming Club'
            },
            {
                'name': 'Fiesta y Premios (Grand Buffet Dinner) and Handing Over Ceremony',
                'date': '2026-09-04',
                'time': '18:00',
                'type': 'social',
                'venue': 'Great Hall',
                'description': 'Grand finale event of the academic year featuring awards ceremony, leadership handover, and elaborate buffet dinner. Celebrate achievements and welcome new leadership.',
                'emoji': '🎊',
                'organised_by': 'CSS Executive Committee'
            }
        ]

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No events will be created'))
            for event_data in events_data:
                self.stdout.write(f"Would create: {event_data['name']} on {event_data['date']}")
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for event_data in events_data:
                try:
                    # Parse date and time
                    event_date = datetime.strptime(event_data['date'], '%Y-%m-%d').date()
                    event_time = time.fromisoformat(event_data['time'])
                    event_datetime = datetime.combine(event_date, event_time)
                    event_datetime = timezone.make_aware(event_datetime)

                    # Handle end date if provided
                    event_end_datetime = None
                    if event_data.get('end_date'):
                        end_date = datetime.strptime(event_data['end_date'], '%Y-%m-%d').date()
                        end_time = time(23, 59)  # End of day for multi-day events
                        event_end_datetime = datetime.combine(end_date, end_time)
                        event_end_datetime = timezone.make_aware(event_end_datetime)

                    # Check if event already exists
                    existing_event = Event.objects.filter(
                        event_name=event_data['name'],
                        event_date=event_datetime
                    ).first()

                    if existing_event and not options['force']:
                        self.stdout.write(
                            self.style.WARNING(f'Skipped: {event_data["name"]} (already exists)')
                        )
                        skipped_count += 1
                        continue

                    # Create or update event
                    event_obj, created = Event.objects.update_or_create(
                        event_name=event_data['name'],
                        event_date=event_datetime,
                        defaults={
                            'description': event_data['description'],
                            'event_end_date': event_end_datetime,
                            'event_type': event_data['type'],
                            'venue': event_data['venue'],
                            'organised_by': event_data['organised_by'],
                            'emoji': event_data.get('emoji', '📅'),
                            'requires_registration': False,  # All events are free and open
                            'requires_payment': False,
                            'allows_rsvp': True,
                            'featured': True if event_data['type'] in ['conference', 'competition'] else False,
                            'sync_memo_enabled': True,
                            'location_type': 'physical',
                            'building': 'KNUST Campus',
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created: {event_data["name"]} on {event_data["date"]}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Updated: {event_data["name"]} on {event_data["date"]}')
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating {event_data["name"]}: {str(e)}')
                    )
                    continue

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Events Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Events Updated: {updated_count}'))
        self.stdout.write(self.style.WARNING(f'Events Skipped: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total Events Processed: {len(events_data)}'))
        self.stdout.write('='*50)

        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ CSS Events Calendar 2025-26 has been successfully loaded!'
                )
            )
            self.stdout.write(
                'You can now view these events in the admin panel or through the API endpoints.'
            )