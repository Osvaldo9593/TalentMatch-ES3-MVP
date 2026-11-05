import logging
import json
from typing import Any, Dict
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenRouterService:
    """
    Servicio aislado para la integración y verificación de conexión con la API de OpenRouter.
    Maneja la autenticación, peticiones HTTP y control de errores sin exponer credenciales.
    """

    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self.model = settings.OPENROUTER_MODEL
        self.timeout = 45.0

    def is_configured(self) -> bool:
        """Verifica si la variable OPENROUTER_API_KEY está definida y no vacía."""
        api_key = settings.OPENROUTER_API_KEY
        return bool(api_key and api_key.strip())

    async def test_connection(self) -> Dict[str, Any]:
        """
        Ejecuta una llamada mínima de prueba contra OpenRouter para validar conectividad,
        autenticación y funcionamiento del modelo configurado.
        """
        if not self.is_configured():
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": "OPENROUTER_API_KEY no está configurada."
            }

        endpoint_url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "TalentMatch API"
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": "Responde únicamente con: OpenRouter OK"
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint_url,
                    json=payload,
                    headers=headers
                )

            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError as exc:
                    logger.exception("OpenRouter devolvió JSON inválido")
                    return {
                        "status": "error",
                        "provider": "openrouter",
                        "model": self.model,
                        "error": f"Respuesta JSON inválida de OpenRouter: {exc}",
                    }
                choices = data.get("choices", [])
                if choices and "message" in choices[0] and "content" in choices[0]["message"]:
                    content = choices[0]["message"]["content"].strip()
                else:
                    content = "OpenRouter OK"

                return {
                    "status": "ok",
                    "provider": "openrouter",
                    "model": self.model,
                    "message": content
                }

            elif response.status_code in (401, 403):
                logger.warning(f"Error de autenticación con OpenRouter (HTTP {response.status_code})")
                return {
                    "status": "error",
                    "provider": "openrouter",
                    "model": self.model,
                    "error": "Error de autenticación con OpenRouter: API Key inválida o sin permisos."
                }

            elif response.status_code == 429:
                logger.warning("OpenRouter rate limit alcanzado")
                return {
                    "status": "error",
                    "provider": "openrouter",
                    "model": self.model,
                    "error": "Límite de peticiones (Rate limit) excedido en OpenRouter. Por favor espera unos momentos."
                }

            elif 500 <= response.status_code <= 599:
                logger.error(f"Error de servidor en OpenRouter (HTTP {response.status_code})")
                return {
                    "status": "error",
                    "provider": "openrouter",
                    "model": self.model,
                    "error": f"Error en los servidores de OpenRouter (HTTP {response.status_code})."
                }

            else:
                logger.warning(f"Respuesta no exitosa de OpenRouter (HTTP {response.status_code})")
                return {
                    "status": "error",
                    "provider": "openrouter",
                    "model": self.model,
                    "error": f"OpenRouter respondió con código de estado HTTP {response.status_code}."
                }

        except httpx.TimeoutException as exc:
            logger.error("Tiempo de espera agotado al conectar con OpenRouter")
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": f"Tiempo de espera agotado al conectar con OpenRouter: {exc}"
            }
        except httpx.HTTPStatusError as exc:
            logger.exception("OpenRouter respondió con un estado HTTP inesperado")
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": f"Error HTTP de OpenRouter: {exc.response.status_code}",
            }
        except httpx.RequestError as exc:
            logger.error(f"Error de red al conectar con OpenRouter: {type(exc).__name__}")
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": "Error de red o conexión al comunicarse con OpenRouter."
            }
        except Exception as exc:
            logger.error(f"Error inesperado con OpenRouter: {type(exc).__name__}")
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": "Error inesperado al procesar la solicitud con OpenRouter."
            }

    async def generate_chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.2,
        response_format: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Envía un conjunto de mensajes a OpenRouter para generar una respuesta mediante el modelo configurado.
        Reutiliza la autenticación, configuración y manejo de errores seguro sin exponer la API key.
        """
        if not self.is_configured():
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": "OPENROUTER_API_KEY no está configurada."
            }

        endpoint_url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "TalentMatch API"
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint_url,
                    json=payload,
                    headers=headers
                )

            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError as exc:
                    logger.exception("OpenRouter devolvió JSON inválido")
                    return {
                        "status": "error",
                        "provider": "openrouter",
                        "model": self.model,
                        "error": f"Respuesta JSON inválida de OpenRouter: {exc}",
                    }
                choices = data.get("choices", [])
                if choices and "message" in choices[0] and "content" in choices[0]["message"]:
                    content = choices[0]["message"]["content"]
                    return {
                        "status": "ok",
                        "provider": "openrouter",
                        "model": self.model,
                        "content": content
                    }
                else:
                    return {
                        "status": "error",
                        "provider": "openrouter",
                        "model": self.model,
                        "error": "OpenRouter no devolvió contenido en la respuesta."
                    }

            elif response.status_code in (401, 403):
                logger.warning(f"Error de autenticación con OpenRouter (HTTP {response.status_code})")
                return {
                    "status": "error",
                    "provider": "openrouter",
                    "model": self.model,
                    "error": "Error de autenticación con OpenRouter: API Key inválida o sin permisos."
                }

            elif response.status_code == 429:
                logger.warning("OpenRouter rate limit alcanzado")
                return {
                    "status": "error",
                    "provider": "openrouter",
                    "model": self.model,
                    "error": "Límite de peticiones (Rate limit) excedido en OpenRouter. Por favor espera unos momentos."
                }

            elif 500 <= response.status_code <= 599:
                logger.error(f"Error de servidor en OpenRouter (HTTP {response.status_code})")
                return {
                    "status": "error",
                    "provider": "openrouter",
                    "model": self.model,
                    "error": f"Error en los servidores de OpenRouter (HTTP {response.status_code})."
                }

            else:
                logger.warning(f"Respuesta no exitosa de OpenRouter (HTTP {response.status_code})")
                return {
                    "status": "error",
                    "provider": "openrouter",
                    "model": self.model,
                    "error": f"OpenRouter respondió con código de estado HTTP {response.status_code}."
                }

        except httpx.TimeoutException as exc:
            logger.error("Tiempo de espera agotado al conectar con OpenRouter")
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": f"Tiempo de espera agotado al conectar con OpenRouter: {exc}"
            }
        except httpx.HTTPStatusError as exc:
            logger.exception("OpenRouter respondió con un estado HTTP inesperado")
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": f"Error HTTP de OpenRouter: {exc.response.status_code}",
            }
        except httpx.RequestError as exc:
            logger.error(f"Error de red al conectar con OpenRouter: {type(exc).__name__}")
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": "Error de red o conexión al comunicarse con OpenRouter."
            }
        except Exception as exc:
            logger.error(f"Error inesperado con OpenRouter: {type(exc).__name__}")
            return {
                "status": "error",
                "provider": "openrouter",
                "model": self.model,
                "error": "Error inesperado al procesar la solicitud con OpenRouter."
            }


openrouter_service = OpenRouterService()
