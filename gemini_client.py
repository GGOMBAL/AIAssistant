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
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        # Validate prompt length
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[Gemini] Prompt length: {len(full_prompt)} chars")

        if len(full_prompt.strip()) < 10:
            logger.error(f"[Gemini] Prompt too short: {len(full_prompt)} chars")
            return "Error: Prompt is too short to generate a meaningful response"

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

                        # Debug: 전체 응답 구조 로깅
                        logger.info(f"[Gemini] Response keys: {list(data.keys())}")

                        candidates = data.get("candidates", [])
                        logger.info(f"[Gemini] Candidates count: {len(candidates)}")

                        if candidates:
                            candidate = candidates[0]
                            logger.info(f"[Gemini] Candidate keys: {list(candidate.keys())}")

                            content = candidate.get("content", {})
                            logger.info(f"[Gemini] Content: {content}")

                            parts = content.get("parts", [])
                            logger.info(f"[Gemini] Parts count: {len(parts)}")

                            if parts:
                                response_text = parts[0].get("text", "").strip()
                                logger.info(f"[Gemini] Response text length: {len(response_text)}")
                                if response_text:
                                    return response_text
                                else:
                                    logger.error("[Gemini] Empty text content")
                                    logger.error(f"[Gemini] Full content structure: {content}")
                                    return "Error: Gemini returned empty text. This may indicate the prompt was too complex or unclear."
                            else:
                                logger.error(f"[Gemini] No parts in content. Content: {content}")
                                logger.error(f"[Gemini] Finish reason: {candidate.get('finishReason', 'unknown')}")
                                logger.error(f"[Gemini] Prompt preview: {full_prompt[:200]}...")
                                return f"Error: Gemini API returned no content. The prompt may be too complex, filtered by safety settings, or missing required context."
                        else:
                            logger.error(f"[Gemini] No candidates. Response: {data}")
                            return f"Gemini returned no candidates."
                    else:
                        error_text = await response.text()
                        logger.error(f"[Gemini] API Error {response.status}: {error_text}")
                        return f"Gemini API Error: {error_text}"

        except Exception as e:
            logger.error(f"[Gemini] Exception: {e}")
            import traceback
            logger.error(traceback.format_exc())
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

        response = await self.generate_response(enhanced_prompt.strip())
        return response