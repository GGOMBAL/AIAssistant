#!/usr/bin/env python3
"""
Gemini API Client
Gemini-2.5-Flash 모델과 직접 통신하는 클라이언트
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.model = "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Gemini API"""

        # Combine system prompt and user prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt

        url = f"{self.base_url}/models/{self.model}:generateContent"
        params = {"key": self.api_key}

        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "topK": 40,
                "maxOutputTokens": 2048,
                "stopSequences": [],
                "candidateCount": 1
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"[DEBUG] Full Gemini response: {json.dumps(data, indent=2, ensure_ascii=False)}")

                        candidates = data.get("candidates", [])
                        if candidates:
                            candidate = candidates[0]
                            print(f"[DEBUG] First candidate: {json.dumps(candidate, indent=2, ensure_ascii=False)}")

                            # Check finish reason
                            finish_reason = candidate.get("finishReason")
                            if finish_reason:
                                print(f"[DEBUG] Finish reason: {finish_reason}")

                            content = candidate.get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                response_text = parts[0].get("text", "").strip()
                                if response_text:
                                    return response_text
                                else:
                                    return "Gemini returned empty text content"
                            else:
                                return f"Gemini returned no parts in content. Content: {json.dumps(content, indent=2, ensure_ascii=False)}"
                        else:
                            return f"Gemini returned no candidates. Full response: {json.dumps(data, indent=2, ensure_ascii=False)}"
                    else:
                        error_text = await response.text()
                        print(f"[DEBUG] API Error: Status {response.status}, Response: {error_text}")
                        return f"Gemini API Error: {error_text}"

        except Exception as e:
            return f"Request failed: {str(e)}"

    async def agent_response(self, agent_name: str, task: str, system_prompt: str) -> str:
        """Get response from specific agent using Gemini"""

        # Enhance the prompt for better agent-specific responses
        enhanced_prompt = f"""
{system_prompt}

You are working as {agent_name} in a multi-agent trading system.
Your specific task is: {task}

Please provide a detailed, professional response that demonstrates your expertise in this area.
If the question is in Korean, please respond in Korean.
If the question is in English, please respond in English.

Make sure to provide a complete and comprehensive answer.
"""

        print(f"[DEBUG] Sending to Gemini for {agent_name}:")
        print(f"[DEBUG] Prompt length: {len(enhanced_prompt)}")
        print(f"[DEBUG] First 200 chars: {enhanced_prompt[:200]}...")

        response = await self.generate_response(enhanced_prompt.strip())

        print(f"[DEBUG] Received response for {agent_name}:")
        print(f"[DEBUG] Response length: {len(response)}")
        print(f"[DEBUG] Response starts with: {response[:100]}...")

        return response