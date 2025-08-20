import os
import json
import uuid
import requests
import google.generativeai as genai
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from projects.models.project_model import Project, ProjectFile
from projects.models.task_model import Task
from projects.models.sprint_model import Sprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini AI

# API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')//working
API_KEY = 'gggggggghggkjkjhkhj'
if API_KEY:
    genai.configure(api_key=API_KEY)

class AISprintAnalysis(APIView):
    permission_classes = (IsAuthenticated,)

    def validate_google_api_key(self):
        """Validate if Google AI API key is properly configured"""
        api_key = os.getenv('GOOGLE_AI_API_KEY')
        
        if not api_key:
            return False, "GOOGLE_AI_API_KEY environment variable not set"
        
        try:
            url = f'https://generativelanguage.googleapis.com/v1/models?key={api_key}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'models' in data and len(data['models']) > 0:
                    return True, f"Valid API key. {len(data['models'])} models available"
                else:
                    return False, "API key valid but no models accessible"
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown API error')
                return False, f"API key invalid: {error_msg}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error validating API key: {str(e)}"
        except Exception as e:
            return False, f"Failed to validate API key: {str(e)}"

    def post(self, request):
        try:
            # Validate API key first
            is_valid, validation_message = self.validate_google_api_key()
            print(f"API Key Validation: {validation_message}")
            
            project_id = request.data.get('project_id')
            file_ids = request.data.get('file_ids', [])
            sprint_id = request.data.get('sprint_id')

            if not project_id:
                return Response({
                    'status': False,
                    'message': 'project_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)

            files = ProjectFile.objects.filter(id__in=file_ids, project=project) if file_ids else []
            document_content = self.extract_document_content(files)

            # Try AI analysis if API key is valid
            if is_valid:
                try:
                    print("AI analysis with Gemini...")
                    ai_analysis = self.analyze_with_gemini(document_content, project.name)
                    suggested_cards = self.process_gemini_response(ai_analysis)
                    
                    if suggested_cards:
                        print(f"AI generated {len(suggested_cards)} cards successfully")
                    else:
                        print("AI returned no cards, using fallback")
                        suggested_cards = self.generate_intelligent_fallback(document_content, project.name)
                        
                except Exception as e:
                    print(f'Gemini API error: {str(e)}')
                    suggested_cards = self.generate_intelligent_fallback(document_content, project.name)
            else:
                print(f"API key invalid, using fallback: {validation_message}")
                suggested_cards = self.generate_intelligent_fallback(document_content, project.name)

            priority_suggestion = self.get_priority_suggestion(suggested_cards)

            analysis_result = {
                'features_count': len(suggested_cards),
                'complexity_score': min(10, max(3, len(suggested_cards))),
                'estimated_days': len(suggested_cards) * 2 + 5,
                'files_analyzed': len(files),
                'ai_confidence': 85 if is_valid and files else 70,
                'using_ai': is_valid,
                'api_status': validation_message
            }

            return Response({
                'status': True,
                'records': {
                    'analysis': analysis_result,
                    'suggested_cards': suggested_cards,
                    'priority_suggestion': priority_suggestion
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'AI analysis failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def extract_document_content(self, files):
        """Extract basic content from files"""
        content_parts = []
        
        for file in files:
            try:
                file_info = f"File: {file.filename}"
                if hasattr(file, 'extension') and file.extension:
                    file_info += f" ({file.extension.upper()})"
                if hasattr(file, 'size'):
                    file_info += f" [{round(file.size/1024)}KB]"
                content_parts.append(file_info)
            except Exception as e:
                print(f'File processing error: {str(e)}')
                content_parts.append(f"File: {getattr(file, 'filename', 'unknown')}")

        return '\n'.join(content_parts) if content_parts else 'No documents provided'

    def analyze_with_gemini(self, document_content, project_name):
        """Use Google Gemini AI to analyze and generate sprint tasks"""
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""You are an expert Agile project manager. Create 5-7 development sprint tasks for this project.

Project Name: {project_name}
Documents: {document_content}

Return ONLY a valid JSON array with these fields: title, description, task_type, priority, story_points, acceptance_criteria

Example:
[{{"title": "Setup Environment", "description": "Configure development environment", "task_type": "TASK", "priority": "HIGH", "story_points": 3, "acceptance_criteria": ["Environment configured", "Team can run project"]}}]

Focus on realistic development tasks."""

            print(f"Sending prompt to Gemini (length: {len(prompt)} chars)")
            response = model.generate_content(prompt)
            print(f"Received response from Gemini (length: {len(response.text)} chars)")
            
            return response.text

        except Exception as e:
            print(f'Gemini API call failed: {str(e)}')
            raise e

    def process_gemini_response(self, ai_response):
        """Process Gemini AI response and extract tasks"""
        try:
            if not ai_response or not ai_response.strip():
                return []

            clean_response = ai_response.strip()
            
            # Remove markdown formatting
            if 'json' in clean_response.lower():
                start_bracket = clean_response.find('[')
                end_bracket = clean_response.rfind(']')
                if start_bracket >= 0 and end_bracket > start_bracket:
                    clean_response = clean_response[start_bracket:end_bracket+1]

            # Parse JSON
            try:
                tasks_data = json.loads(clean_response)
            except json.JSONDecodeError:
                print("Could not extract JSON from AI response")
                return []

            # Handle different response formats
            if isinstance(tasks_data, dict) and 'tasks' in tasks_data:
                tasks = tasks_data['tasks']
            elif isinstance(tasks_data, list):
                tasks = tasks_data
            else:
                return []

            # Process each task
            processed_cards = []
            for i, task in enumerate(tasks):
                try:
                    if not task.get('title'):
                        continue

                    card = {
                        'ai_id': str(uuid.uuid4()),
                        'title': task.get('title', f'AI Task {i+1}'),
                        'description': task.get('description', 'Generated by AI'),
                        'task_type': task.get('task_type', 'TASK').upper(),
                        'priority': task.get('priority', 'MEDIUM').upper(),
                        'story_points': min(8, max(1, int(task.get('story_points', 3)))),
                        'acceptance_criteria': task.get('acceptance_criteria', [
                            'Task completed as specified',
                            'Code reviewed and tested',
                            'Documentation updated'
                        ])
                    }
                    
                    # Validate task_type
                    if card['task_type'] not in ['TASK', 'STORY', 'BUG', 'EPIC']:
                        card['task_type'] = 'TASK'
                    
                    # Validate priority
                    if card['priority'] not in ['HIGH', 'MEDIUM', 'LOW']:
                        card['priority'] = 'MEDIUM'

                    processed_cards.append(card)
                    
                except Exception as e:
                    print(f'Error processing task {i}: {str(e)}')
                    continue

            return processed_cards[:7]

        except Exception as e:
            print(f'Response processing error: {str(e)}')
            return []

    def generate_intelligent_fallback(self, document_content, project_name):
        """Generate intelligent fallback tasks based on project context"""
        print(f"Generating fallback cards for project: {project_name}")
        
        content_lower = document_content.lower()
        
        fallback_cards = [
            {
                'ai_id': str(uuid.uuid4()),
                'title': f'{project_name} - Development Environment Setup',
                'description': f'Configure development environment and project structure for {project_name}',
                'task_type': 'TASK',
                'priority': 'HIGH',
                'story_points': 3,
                'acceptance_criteria': [
                    'Development environment configured',
                    'Project structure established',
                    'Team can run project locally',
                    'Basic CI/CD pipeline setup'
                ]
            },
            {
                'ai_id': str(uuid.uuid4()),
                'title': f'{project_name} - Database Design and Implementation',
                'description': 'Design and implement core database schema with proper relationships',
                'task_type': 'TASK',
                'priority': 'HIGH',
                'story_points': 5,
                'acceptance_criteria': [
                    'Database schema designed',
                    'Models and relationships defined',
                    'Database migrations created',
                    'Data validation implemented'
                ]
            }
        ]

        # Add context-specific cards
        if any(keyword in content_lower for keyword in ['user', 'auth', 'login']):
            fallback_cards.append({
                'ai_id': str(uuid.uuid4()),
                'title': f'{project_name} - User Authentication System',
                'description': 'Implement user registration, login, and authentication',
                'task_type': 'STORY',
                'priority': 'HIGH',
                'story_points': 8,
                'acceptance_criteria': [
                    'User registration functionality',
                    'Secure login/logout system',
                    'Password management',
                    'Session handling'
                ]
            })

        if any(keyword in content_lower for keyword in ['api', 'endpoint', 'rest']):
            fallback_cards.append({
                'ai_id': str(uuid.uuid4()),
                'title': f'{project_name} - REST API Development',
                'description': 'Develop REST API endpoints for core features',
                'task_type': 'TASK',
                'priority': 'MEDIUM',
                'story_points': 5,
                'acceptance_criteria': [
                    'RESTful endpoints implemented',
                    'Proper HTTP status codes',
                    'API documentation created'
                ]
            })

        if any(keyword in content_lower for keyword in ['ui', 'frontend', 'interface']):
            fallback_cards.append({
                'ai_id': str(uuid.uuid4()),
                'title': f'{project_name} - Frontend UI Components',
                'description': 'Create responsive user interface components',
                'task_type': 'TASK',
                'priority': 'MEDIUM',
                'story_points': 5,
                'acceptance_criteria': [
                    'UI components developed',
                    'Responsive design implemented',
                    'Component testing'
                ]
            })

        fallback_cards.append({
            'ai_id': str(uuid.uuid4()),
            'title': f'{project_name} - Testing and Quality Assurance',
            'description': 'Implement testing strategy and quality assurance',
            'task_type': 'TASK',
            'priority': 'MEDIUM',
            'story_points': 3,
            'acceptance_criteria': [
                'Unit tests implemented',
                'Integration tests created',
                'Test coverage report'
            ]
        })

        return fallback_cards

    def get_priority_suggestion(self, cards):
        """Get priority suggestion for first task to work on"""
        if not cards:
            return None

        setup_keywords = ['setup', 'environment', 'configuration', 'database', 'schema']

        for card in cards:
            title_lower = card['title'].lower()
            if any(keyword in title_lower for keyword in setup_keywords):
                result_card = card.copy()
                result_card['confidence'] = 90
                result_card['reasoning'] = [
                    'Foundation task that enables other development',
                    'Essential for team productivity',
                    'Reduces project risk',
                    'Allows parallel development'
                ]
                return result_card

        high_priority_cards = [c for c in cards if c['priority'] == 'HIGH']
        if high_priority_cards:
            result_card = high_priority_cards[0].copy()
            result_card['confidence'] = 80
            result_card['reasoning'] = [
                'High priority task for project success',
                'Important feature for user experience',
                'Should be completed early'
            ]
            return result_card

        return None


class AICreateSprintTasks(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            sprint_id = request.data.get('sprint_id')
            cards = request.data.get('cards', [])

            if not project_id or not cards:
                return Response({
                    'status': False,
                    'message': 'project_id and cards are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)

            sprint = None
            if sprint_id:
                sprint = Sprint.objects.filter(id=sprint_id).first()

            created_tasks = []

            for card_data in cards:
                try:
                    if not card_data.get('title'):
                        continue

                    task = Task.objects.create(
                        title=card_data['title'],
                        description=card_data.get('description', ''),
                        task_type=card_data.get('task_type', 'TASK'),
                        priority=card_data.get('priority', 'MEDIUM'),
                        story_points=card_data.get('story_points'),
                        project=project,
                        sprint=sprint,
                        status='TODO',
                        labels=card_data.get('acceptance_criteria', [])
                    )

                    created_tasks.append({
                        'id': str(task.id),
                        'title': task.title,
                        'ai_id': card_data.get('ai_id'),
                        'priority': task.priority
                    })

                except Exception as e:
                    print(f'Error creating task: {str(e)}')
                    continue

            return Response({
                'status': True,
                'message': f'{len(created_tasks)} tasks created successfully',
                'records': created_tasks
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to create tasks',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TestGoogleAI(APIView):
    """Test endpoint to check Google AI API configuration"""
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        api_key = os.getenv('GOOGLE_AI_API_KEY')
        
        if not api_key:
            return Response({
                'status': False,
                'message': 'GOOGLE_AI_API_KEY not configured',
                'help': 'Set GOOGLE_AI_API_KEY environment variable'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Respond with: API test successful")
            
            return Response({
                'status': True,
                'message': 'Google AI API is working correctly',
                'test_response': response.text,
                'api_key_preview': api_key[:10] + '...'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': f'Google AI API test failed: {str(e)}',
                'help': 'Check your API key at https://aistudio.google.com/app/apikey'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
