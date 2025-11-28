import json
import concurrent.futures
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import AIChatMessage
from workspaces.models import Workspace
from workspaces.models import WorkspaceMember

# --- THIS IS THE ONLY IMPORT YOU NEED ---
# Your new engine.py handles ALL the logic (routing, Q&A, etc.)
from .engine import get_chatbot_response


@login_required
@require_POST
def ask_question(request):
    """
    API endpoint for the PRIVATE AI chatbot.
    This view is now SIMPLE. It just passes the request to the engine.
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
        
        try:
            member = WorkspaceMember.objects.get(workspace=workspace, user=request.user)
            if member.role == WorkspaceMember.Role.REVIEWER:
                return JsonResponse({'error': 'Reviewers do not have access to AI ChatBot.'}, status=403)
        except WorkspaceMember.DoesNotExist:
            return JsonResponse({'error': 'You are not a member of this workspace.'}, status=403)
        
        # --- 1. Save User's Question ---
        user_message = AIChatMessage.objects.create(
            user=request.user,
            workspace=workspace,
            message=question_text,
            is_from_bot=False
        )
        
        # --- 2. Get AI's Answer ---
        # The engine.py now handles ALL logic (routing, summary, abstract, Q&A)
        # Run LLM calls in a thread pool to prevent blocking
        ai_prompt = question_text.lstrip('/ai').strip()
        
        # Use thread pool executor to run blocking LLM calls
        print(f"[ask_question] Starting chatbot response for question: {ai_prompt[:100]}...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(get_chatbot_response, ai_prompt, workspace_id)
            try:
                # Set timeout to 90 seconds for LLM calls (matching frontend timeout)
                print(f"[ask_question] Waiting for response (timeout: 90s)...")
                answer = future.result(timeout=90)
                print(f"[ask_question] Received answer, length: {len(answer) if answer else 0} chars")
            except concurrent.futures.TimeoutError:
                answer = "Sorry, the AI response took too long (over 90 seconds). The question might be too complex or the AI service is slow. Please try again with a simpler question."
                print(f"[ask_question] Timeout error for question: {ai_prompt}")
            except Exception as e:
                answer = f"Error generating response: {str(e)}"
                print(f"[ask_question] Error in chatbot response: {e}")
                import traceback
                traceback.print_exc()
        
        # --- 3. Save AI's Answer ---
        ai_message = AIChatMessage.objects.create(
            user=request.user,
            workspace=workspace,
            message=answer,
            is_from_bot=True
        )
        
        # --- 4. Return both messages to the frontend ---
        return JsonResponse({
            'status': 'ok',
            'user_question': user_message.message,
            'ai_answer': ai_message.message
        })

    except Exception as e:
        print(f"Error in ask_question view: {e}")
        return JsonResponse({'error': f'An internal error occurred: {e}'}, status=500)