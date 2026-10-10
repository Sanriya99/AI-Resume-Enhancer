import json
import os

from openai import OpenAI


def analyze_resume(resume_text, user_goal):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"skills": [], "missing_skills": [], "roadmap": [], "interview_questions": [],
                "error": "OPENAI_API_KEY is not set. Add your OpenAI API key to the .env file."}

    client = OpenAI(api_key=api_key)
    prompt = f'''You are a senior software engineer and hiring manager.
Evaluate the resume for the user's target role.
Target role: {user_goal}

Rules:
- Extract only skills relevant to this goal.
- Identify realistic skill gaps.
- Create a roadmap only for missing skills.
- Tailor the output to the target role.
- Return valid JSON only, with this exact structure:
{{
  "skills": [],
  "missing_skills": [],
  "roadmap": [],
  "interview_questions": []
}}

Resume:
{resume_text}
'''
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You are a careful, practical hiring manager. Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        content = (response.choices[0].message.content or "").strip()
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end < start:
            raise ValueError("The AI response did not contain valid JSON.")
        data = json.loads(content[start:end + 1])
        for key in ("skills", "missing_skills", "roadmap", "interview_questions"):
            data.setdefault(key, [])
        return data
    except Exception as exc:
        return {"skills": [], "missing_skills": [], "roadmap": [], "interview_questions": [],
                "error": f"AI analysis failed: {exc}"}
