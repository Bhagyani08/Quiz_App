"""
LLM-Based Quiz Answer Evaluator
Uses Azure OpenAI GPT-4o-mini to evaluate quiz answers and generate scores
"""

import json
import time
from typing import List, Dict, Any
import config

# =============================================================
# EVALUATION PROMPTS
# =============================================================

SYSTEM_PROMPT = """You are an expert AI/ML educator tasked with evaluating student quiz answers.

**Your Responsibilities:**
1. Evaluate each answer based on correctness, completeness, and relevance to the question
2. Assign a score between 0.0 and 1.0 for each answer:
   - 1.0: Correct, comprehensive, and well-explained answer
   - 0.7-0.9: Correct but incomplete or missing some details
   - 0.4-0.6: Partially correct, contains some relevant information but also errors
   - 0.1-0.3: Mostly incorrect but shows some understanding
   - 0.0: Wrong, irrelevant, or empty answer

3. Be fair and consistent in your evaluation
4. Consider that these are short-form answers, not essays
5. Give credit for correct concepts even if wording is informal

**CRITICAL: Output Format**
You MUST respond with ONLY a valid JSON array of numbers (scores), one for each question.
Do NOT include any explanations, comments, or additional text.
Format: [score1, score2, score3, ..., score31]

Example output:
[1.0, 0.8, 0.5, 0.0, 1.0, 0.7, 0.9, 0.5, 0.6, 1.0, 0.8, 0.0, 0.9, 0.7, 0.5, 1.0, 0.8, 0.6, 0.9, 1.0, 0.7, 0.5, 0.8, 0.9, 1.0, 0.6, 0.7, 0.8, 0.9, 1.0, 0.5]
"""

def create_user_prompt(questions_and_answers: List[Dict[str, str]]) -> str:
    """
    Create the user prompt with all question-answer pairs
    
    Args:
        questions_and_answers: List of dicts with 'question' and 'answer' keys
    
    Returns:
        Formatted prompt string
    """
    prompt = "Evaluate the following quiz answers and provide scores (0.0 to 1.0) for each:\n\n"
    
    for idx, qa in enumerate(questions_and_answers, 1):
        question = qa['question']
        answer = qa['answer'].strip()
        
        # Handle empty answers
        if not answer:
            answer = "[No answer provided]"
        
        prompt += f"Question {idx}: {question}\n"
        prompt += f"Answer {idx}: {answer}\n\n"
    
    num_questions = len(questions_and_answers)
    prompt += f"Remember: Respond with ONLY a JSON array of {num_questions} scores, nothing else."
    
    return prompt

# =============================================================
# LLM EVALUATION FUNCTION
# =============================================================

def evaluate_answers_with_llm(
    questions_and_answers: List[Dict[str, str]],
    max_retries: int = 3
) -> List[float]:
    """
    Use Azure OpenAI to evaluate quiz answers and return scores
    
    Args:
        questions_and_answers: List of Q&A dicts
        max_retries: Number of retry attempts if API fails
    
    Returns:
        List of scores (floats between 0.0 and 1.0), one per question
    
    Raises:
        ValueError: If response cannot be parsed or has wrong length
        Exception: If API call fails after retries
    """
    num_questions = len(questions_and_answers)
    
    if num_questions == 0:
        raise ValueError("No questions provided for evaluation")
    
    user_prompt = create_user_prompt(questions_and_answers)
    
    for attempt in range(max_retries):
        try:
            print(f"   🤖 Calling Azure OpenAI API (attempt {attempt + 1}/{max_retries})...")
            
            response = config.chat_client.chat.completions.create(
                model=config.AZURE_CHAT_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Low temperature for consistent scoring
                max_tokens=500,   # Enough for array of 31 scores
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Extract the response
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                # Handle case where LLM wraps array in object
                parsed = json.loads(result_text)
                
                if isinstance(parsed, dict):
                    # Look for array in common keys
                    scores = parsed.get('scores') or parsed.get('result') or parsed.get('evaluations')
                    if scores is None:
                        # If no known key, try to find first list value
                        for value in parsed.values():
                            if isinstance(value, list):
                                scores = value
                                break
                elif isinstance(parsed, list):
                    scores = parsed
                else:
                    raise ValueError(f"Unexpected JSON structure: {type(parsed)}")
                
                # Validate scores
                if not isinstance(scores, list):
                    raise ValueError(f"Scores is not a list: {type(scores)}")
                
                if len(scores) != num_questions:
                    raise ValueError(f"Expected {num_questions} scores, got {len(scores)}")
                
                # Convert to floats and validate range
                validated_scores = []
                for i, score in enumerate(scores):
                    try:
                        float_score = float(score)
                        if not (0.0 <= float_score <= 1.0):
                            print(f"   ⚠️  Score {i+1} out of range: {float_score}, clamping to [0.0, 1.0]")
                            float_score = max(0.0, min(1.0, float_score))
                        validated_scores.append(float_score)
                    except (ValueError, TypeError):
                        print(f"   ⚠️  Invalid score at position {i+1}: {score}, using 0.0")
                        validated_scores.append(0.0)
                
                print(f"   ✅ Successfully received {len(validated_scores)} scores")
                return validated_scores
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parsing error: {e}")
                print(f"   Response was: {result_text[:200]}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise ValueError(f"Failed to parse JSON after {max_retries} attempts")
        
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"   ⏳ Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"API call failed after {max_retries} attempts: {e}")
    
    # Should never reach here
    raise Exception("Evaluation failed unexpectedly")

# =============================================================
# HELPER FUNCTION: CALCULATE TOTAL SCORE
# =============================================================

def calculate_total_score(scores: List[float]) -> Dict[str, float]:
    """
    Calculate total score and percentage
    
    Args:
        scores: List of individual scores
    
    Returns:
        Dict with total_score, max_score, and percentage
    """
    total = sum(scores)
    max_possible = len(scores) * 1.0
    percentage = (total / max_possible * 100) if max_possible > 0 else 0.0
    
    return {
        "total_score": round(total, 2),
        "max_score": max_possible,
        "percentage": round(percentage, 2)
    }
