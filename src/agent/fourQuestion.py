





from src.configurations.llm import OpenAiConfig
from src.common.logger import get_logger
from src.common.models import DiscussionQuestionsResponse, DiscussionQuestion
logger = get_logger("FOUR_QUESTIONS_AGENT")




def four_questions_agent(course_name, course_description, open_ai_model, open_ai_key):
    try:  
        openai = OpenAiConfig(open_ai_key)
        messages = [{
            "role": "system",
            "content": f"""
               You are a class discussion assistant that excels at writing four open-ended discussion questions for university courses.
                Generate four open-ended discussion questions for a course that follows the following format. 

                An open-ended discussion question inspired by the course description and the name of the course provided. 
                A different open-ended discussion question inspired by the course description and the name of the course provided. 
                A different open-ended discussion question inspired by the course description and the name of the course provided. 
                An open-ended discussion question inspired by the course description and the name of the course provided.

                Only generate 4 short and interesting questions. Keep each questions very specific; these will be used during specific weeks of the course so they should ask targeted questions directed at a specific aspect of the course. For example, if the course is called “Large Language Models 101” and the description is “This course introduces CS students to using Large Language models in production”, DO NOT ask a question like “How can companies use LLMs to improve performance” and DO ASK “What can be some shortcomings when using only cosine similarity search for Retrieval Augmented Generation systems?”
 
                Rules: You always create your question to be as specific as possible. You always ask questions that are 12 words or less. Make sure that the questions are different than
                
                Here’s the summary of what we know about the class:
                course_name: {course_name}
                course_description: {course_description}
            """
        }]

        
           
        try:
            response, completion_tokens, prompt_tokens = openai.generate_response(messages=messages, model=open_ai_model)
            print(f"completion_tokens: {completion_tokens}, prompt_tokens: {prompt_tokens}")
        except Exception as e:
            logger.error(f"Error in four_questions response agent: {e}")
            return None, 0, 0


        # Extract the questions from the response and structure them in the Pydantic model
        questions_text = response.strip().split('\n')
        questions = [
            DiscussionQuestion(question=q.strip().lstrip("0123456789.").strip())  # Remove numbers and spaces at the beginning
            for q in questions_text if q.strip()  # Only include non-empty lines
        ]

        # Return the Pydantic response model
        return DiscussionQuestionsResponse(questions=questions, total_completion_tokens=completion_tokens, total_prompt_tokens=prompt_tokens)

    except Exception as e:  
        logger.error(f"Error in four_questions_agent: {e}")  
        return None,0,0
