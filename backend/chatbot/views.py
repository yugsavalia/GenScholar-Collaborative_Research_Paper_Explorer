import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import AIChatMessage
from workspaces.models import Workspace
from .engine import get_chatbot_response


@login_required
@require_POST
def ask_question(request):
    """
    API endpoint for the PRIVATE AI chatbot.
    1. Saves the user's question to the private AIChatMessage model.
    2. Gets an answer from the engine.
    3. Saves the AI's answer to the private AIChatMessage model.
    4. Returns BOTH messages as JSON to the frontend.
    
    This view NO LONGER broadcasts over WebSockets.
    """
    try:
        data = json.loads(request.body)
        question_text = data.get('question')
        workspace_id = data.get('workspace_id')

        if not question_text:
            return JsonResponse({'error': 'No "question" provided.'}, status=400)
        if not workspace_id:
            return JsonResponse({'error': 'No "workspace_id" provided.'}, status=400)

        # --- Get models and check permissions ---
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return JsonResponse({'error': 'Workspace not found.'}, status=404)
        
        if not workspace.members.filter(user=request.user).exists():
            return JsonResponse({'error': 'You do not have permission to access this workspace.'}, status=403)
        
        # --- 1. Save User's Question ---
        
        user_message = AIChatMessage.objects.create(
            user=request.user,
            workspace=workspace,
            message=question_text,
            is_from_bot=False
        )
        
        # --- 2. Get AI's Answer ---
        ai_prompt = question_text.lstrip('/ai').strip()
        answer = get_chatbot_response(ai_prompt, workspace_id)
        
        
        ai_message = AIChatMessage.objects.create(
            user=request.user,
            workspace=workspace,
            message=answer,
            is_from_bot=True
        )
        
        return JsonResponse({
            'status': 'ok',
            'user_question': user_message.message,
            'ai_answer': ai_message.message
        })

    except Exception as e:
        print(f"Error in ask_question view: {e}")
        return JsonResponse({'error': f'An internal error occurred: {e}'}, status=500)