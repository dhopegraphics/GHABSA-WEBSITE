"""
Data migration to populate initial mentorship areas and skill tags.
Based on SchoolOfGroups.txt requirements document.
"""

from django.db import migrations
from django.utils.text import slugify


def populate_mentorship_data(apps, schema_editor):
    """Populate initial mentorship areas and skill tags."""
    MentorshipArea = apps.get_model('mentorship', 'MentorshipArea')
    SkillTag = apps.get_model('mentorship', 'SkillTag')
    
    # Define mentorship areas with their details
    areas_data = [
        {
            'name': 'Cyber Security',
            'description': 'Learn about network security, ethical hacking, penetration testing, and protecting systems from cyber threats.',
            'icon': 'shield',
            'color': '#EF4444',  # Red
            'order': 1,
            'tags': [
                'Network Security',
                'Ethical Hacking',
                'Penetration Testing',
                'Cryptography',
                'Security Auditing',
                'Incident Response',
                'Malware Analysis',
                'Firewall Configuration',
                'OWASP',
                'Kali Linux',
                'Wireshark',
                'Metasploit',
                'Burp Suite',
                'SIEM',
                'SOC Operations',
            ]
        },
        {
            'name': 'Web Development',
            'description': 'Full-stack web development including frontend, backend, databases, and deployment.',
            'icon': 'globe',
            'color': '#3B82F6',  # Blue
            'order': 2,
            'tags': [
                'HTML/CSS',
                'JavaScript',
                'TypeScript',
                'React',
                'Next.js',
                'Vue.js',
                'Angular',
                'Node.js',
                'Express.js',
                'Django',
                'Flask',
                'FastAPI',
                'REST APIs',
                'GraphQL',
                'PostgreSQL',
                'MongoDB',
                'Redis',
                'Docker',
                'AWS',
                'Git/GitHub',
            ]
        },
        {
            'name': 'Front-End Development',
            'description': 'Specialize in building user interfaces, responsive designs, and interactive web experiences.',
            'icon': 'layout',
            'color': '#8B5CF6',  # Purple
            'order': 3,
            'tags': [
                'HTML5',
                'CSS3',
                'Sass/SCSS',
                'Tailwind CSS',
                'Bootstrap',
                'JavaScript',
                'TypeScript',
                'React',
                'Vue.js',
                'Angular',
                'Svelte',
                'Next.js',
                'Responsive Design',
                'Web Accessibility',
                'Performance Optimization',
                'State Management',
                'Testing (Jest/Cypress)',
                'Webpack/Vite',
            ]
        },
        {
            'name': 'Back-End Development',
            'description': 'Server-side development, APIs, databases, and system architecture.',
            'icon': 'server',
            'color': '#10B981',  # Green
            'order': 4,
            'tags': [
                'Python',
                'Java',
                'Node.js',
                'Go',
                'Rust',
                'C#/.NET',
                'PHP',
                'Django',
                'Flask',
                'FastAPI',
                'Spring Boot',
                'Express.js',
                'REST APIs',
                'GraphQL',
                'PostgreSQL',
                'MySQL',
                'MongoDB',
                'Redis',
                'Message Queues',
                'Microservices',
                'System Design',
            ]
        },
        {
            'name': 'UI/UX Design',
            'description': 'User interface design, user experience research, prototyping, and design systems.',
            'icon': 'palette',
            'color': '#F59E0B',  # Amber
            'order': 5,
            'tags': [
                'Figma',
                'Adobe XD',
                'Sketch',
                'InVision',
                'Prototyping',
                'Wireframing',
                'User Research',
                'Usability Testing',
                'Information Architecture',
                'Interaction Design',
                'Visual Design',
                'Design Systems',
                'Accessibility Design',
                'Mobile UI Design',
                'Web UI Design',
                'Design Thinking',
            ]
        },
        {
            'name': 'Mobile App Development',
            'description': 'Build native and cross-platform mobile applications for iOS and Android.',
            'icon': 'smartphone',
            'color': '#06B6D4',  # Cyan
            'order': 6,
            'tags': [
                'React Native',
                'Flutter',
                'Swift',
                'Kotlin',
                'iOS Development',
                'Android Development',
                'Expo',
                'Firebase',
                'Mobile UI/UX',
                'App Store Deployment',
                'Push Notifications',
                'Offline Storage',
                'Mobile Security',
                'Performance Optimization',
                'Cross-Platform Development',
            ]
        },
        {
            'name': 'Robotics & IoT',
            'description': 'Explore robotics, embedded systems, Internet of Things, and hardware programming.',
            'icon': 'cpu',
            'color': '#EC4899',  # Pink
            'order': 7,
            'tags': [
                'Arduino',
                'Raspberry Pi',
                'ESP32/ESP8266',
                'C/C++',
                'Python',
                'Embedded Systems',
                'Sensors & Actuators',
                'MQTT',
                'Circuit Design',
                'PCB Design',
                'ROS (Robot Operating System)',
                'Computer Vision',
                'Motor Control',
                '3D Printing',
                'Home Automation',
            ]
        },
        {
            'name': 'Data Science',
            'description': 'Data analysis, visualization, statistical modeling, and deriving insights from data.',
            'icon': 'bar-chart',
            'color': '#14B8A6',  # Teal
            'order': 8,
            'tags': [
                'Python',
                'R',
                'SQL',
                'Pandas',
                'NumPy',
                'Matplotlib',
                'Seaborn',
                'Plotly',
                'Jupyter Notebooks',
                'Statistical Analysis',
                'Data Cleaning',
                'Data Visualization',
                'Excel/Google Sheets',
                'Power BI',
                'Tableau',
                'ETL Processes',
                'Big Data',
            ]
        },
        {
            'name': 'Machine Learning',
            'description': 'Build intelligent systems using machine learning, deep learning, and AI techniques.',
            'icon': 'brain',
            'color': '#6366F1',  # Indigo
            'order': 9,
            'tags': [
                'Python',
                'TensorFlow',
                'PyTorch',
                'Scikit-learn',
                'Keras',
                'Neural Networks',
                'Deep Learning',
                'Natural Language Processing',
                'Computer Vision',
                'Reinforcement Learning',
                'Model Training',
                'Feature Engineering',
                'MLOps',
                'Hugging Face',
                'OpenCV',
                'LLMs & Generative AI',
            ]
        },
        {
            'name': 'Cloud Computing',
            'description': 'Cloud platforms, DevOps practices, and cloud-native application development.',
            'icon': 'cloud',
            'color': '#0EA5E9',  # Sky Blue
            'order': 10,
            'tags': [
                'AWS',
                'Google Cloud Platform',
                'Microsoft Azure',
                'Docker',
                'Kubernetes',
                'Terraform',
                'CI/CD',
                'Linux Administration',
                'Serverless',
                'Cloud Security',
                'Networking',
                'Load Balancing',
                'Auto Scaling',
                'Infrastructure as Code',
                'Monitoring & Logging',
            ]
        },
        {
            'name': 'Game Development',
            'description': 'Create video games using game engines, programming, and game design principles.',
            'icon': 'gamepad',
            'color': '#F97316',  # Orange
            'order': 11,
            'tags': [
                'Unity',
                'Unreal Engine',
                'Godot',
                'C#',
                'C++',
                'Game Design',
                'Level Design',
                '2D Game Development',
                '3D Game Development',
                'Physics Engines',
                'Animation',
                'Shaders',
                'Multiplayer Networking',
                'Game AI',
                'VR/AR Development',
            ]
        },
        {
            'name': 'Blockchain & Web3',
            'description': 'Decentralized applications, smart contracts, and blockchain technology.',
            'icon': 'link',
            'color': '#8B5CF6',  # Violet
            'order': 12,
            'tags': [
                'Solidity',
                'Ethereum',
                'Smart Contracts',
                'Web3.js',
                'Hardhat',
                'Truffle',
                'DeFi',
                'NFTs',
                'IPFS',
                'Cryptocurrency',
                'Wallet Integration',
                'dApp Development',
                'Tokenomics',
                'Blockchain Security',
            ]
        },
        {
            'name': 'Project Management',
            'description': 'Learn agile methodologies, team leadership, and effective project delivery.',
            'icon': 'clipboard',
            'color': '#64748B',  # Slate
            'order': 13,
            'tags': [
                'Agile/Scrum',
                'Kanban',
                'Jira',
                'Trello',
                'Asana',
                'Sprint Planning',
                'Stakeholder Management',
                'Risk Management',
                'Team Leadership',
                'Communication Skills',
                'Time Management',
                'Documentation',
                'Product Management',
                'Technical Writing',
            ]
        },
        {
            'name': 'Competitive Programming',
            'description': 'Algorithm design, problem-solving, and competitive coding skills.',
            'icon': 'code',
            'color': '#DC2626',  # Red
            'order': 14,
            'tags': [
                'Data Structures',
                'Algorithms',
                'Dynamic Programming',
                'Graph Algorithms',
                'Sorting & Searching',
                'Mathematical Programming',
                'C++',
                'Python',
                'Java',
                'LeetCode',
                'Codeforces',
                'HackerRank',
                'Problem Solving',
                'Time Complexity Analysis',
            ]
        },
        {
            'name': 'Other',
            'description': 'Other mentorship areas not covered by the main categories.',
            'icon': 'more-horizontal',
            'color': '#71717A',  # Gray
            'order': 99,
            'tags': [
                'Career Guidance',
                'Interview Preparation',
                'Resume Building',
                'Soft Skills',
                'Networking',
                'Public Speaking',
                'Technical Writing',
                'Open Source Contribution',
                'Freelancing',
                'Entrepreneurship',
            ]
        },
    ]
    
    # Create areas and their tags
    for area_data in areas_data:
        tags = area_data.pop('tags')
        area_data['slug'] = slugify(area_data['name'])
        
        area = MentorshipArea.objects.create(**area_data)
        
        # Create tags for this area
        for idx, tag_name in enumerate(tags):
            SkillTag.objects.create(
                area=area,
                name=tag_name,
                order=idx + 1
            )
    
    print(f"Created {len(areas_data)} mentorship areas with their skill tags.")


def reverse_populate(apps, schema_editor):
    """Remove all populated data."""
    MentorshipArea = apps.get_model('mentorship', 'MentorshipArea')
    SkillTag = apps.get_model('mentorship', 'SkillTag')
    
    SkillTag.objects.all().delete()
    MentorshipArea.objects.all().delete()


class Migration(migrations.Migration):
    
    dependencies = [
        ('mentorship', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(populate_mentorship_data, reverse_populate),
    ]
