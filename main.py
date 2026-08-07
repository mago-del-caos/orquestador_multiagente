from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import httpx
import asyncio
from itertools import cycle
import sqlite3
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Cargar variables del .env
load_dotenv()

# ==========================================
# LECTURA DE LLAVES SEGURA
# ==========================================
keys_raw = os.getenv("GROQ_KEYS", "")
GLOBAL_KEY_POOL = [key.strip() for key in keys_raw.split(",") if key.strip()]
key_cycle = cycle(GLOBAL_KEY_POOL) if GLOBAL_KEY_POOL else None

# ==========================================
# CONFIGURACIÓN SMTP
# ==========================================
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
CORREO_ADMIN = "profesorxjuvenal@gmail.com" 

TUTORES = {
    "1o de Secundaria": "adrian.rivera@juventud.edu.mx",
    "2o de Secundaria": "adrian.rivera@juventud.edu.mx",
    "3o de Secundaria": "adrian.rivera@juventud.edu.mx",
    "4o de Preparatoria": "adrian.rivera@juventud.edu.mx",
    "5o de Preparatoria": "adrian.rivera@juventud.edu.mx",
    "6o de Preparatoria": "adrian.rivera@juventud.edu.mx"
}

app = FastAPI(title="Chemini API Gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ==========================================
# RUTAS DE ARCHIVOS
# ==========================================
@app.get("/")
def servir_interfaz(): return FileResponse("index.html")
@app.get("/styles.css")
def servir_css(): return FileResponse("styles.css")
@app.get("/manifest.json")
def servir_manifest(): return FileResponse("manifest.json")
@app.get("/sw.js")
def servir_sw(): return FileResponse("sw.js")
@app.get("/logo.png")
def servir_logo(): return FileResponse("logo.png")

# ==========================================
# LÓGICA DE AGENTES
# ==========================================
AGENTES_DISPONIBLES = {
    "Sócrates": "Eres Sócrates. Enfoque: ironía, mayéutica.",
    "Sombrero Blanco": "Datos objetivos.",
    "Sombrero Rojo": "Emociones.",
    "Sombrero Negro": "Pensamiento crítico.",
    "Sombrero Amarillo": "Lógica constructiva.",
    "Sombrero Verde": "Energía creativa.",
    "Sombrero Azul": "Organizador.",
    "IA PNL": "Estrategias prácticas.",
    "Pensamiento Lateral": "Provocador creativo.",
    "IA Psicólogo": "Apoyo emocional.",
    "Profe Adrián": "Experto en IA y herramientas."
}

class PeticionDebate(BaseModel):
    estudiante: str
    grado: str
    agentes_seleccionados: list[str]
    prompt: str
    ciclos_bucle: int = 1
    longitud: str = "Respuesta corta"

# ==========================================
# FILTROS Y SEGURIDAD
# ==========================================
def enviar_alerta_correo(estudiante, grado, prompt):
    tutor = TUTORES.get(grado, CORREO_ADMIN)
    msg = MIMEMultipart()
    msg['Subject'] = f"🚨 ALERTA: {estudiante} ({grado})"
    msg.attach(MIMEText(f"Mensaje bloqueado: {prompt}", 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [tutor, CORREO_ADMIN], msg.as_string())
        server.quit()
    except: pass

@app.post("/debate")
async def procesar_debate(peticion: PeticionDebate):
    # Filtro
    palabras_alerta = ["idiota", "estúpido", "matarme", "suicidio", "morir", "pendejo"]
    if any(p in peticion.prompt.lower() for p in palabras_alerta):
        asyncio.create_task(asyncio.to_thread(enviar_alerta_correo, peticion.estudiante, peticion.grado, peticion.prompt))
        raise HTTPException(status_code=403, detail="Contenido de riesgo detectado.")

    texto_debate = ""
    diccionario_respuestas = {}
    
    # Configurar tiempos
    tiempos = {"Respuesta corta": 0.5, "Razonamiento": 4.0, "Razonamiento profundo": 6.0}
    tiempo_espera = tiempos.get(peticion.longitud, 0.5)

    for _ in range(peticion.ciclos_bucle):
        for agente in peticion.agentes_seleccionados:
            headers = {"Authorization": f"Bearer {next(key_cycle)}", "Content-Type": "application/json"}
            payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": peticion.prompt}]}
            
            async with httpx.AsyncClient() as client:
                res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30.0)
                contenido = res.json()["choices"][0]["message"]["content"]
            
            diccionario_respuestas[agente] = contenido
            await asyncio.sleep(tiempo_espera)

    return {"analisis_individuales": diccionario_respuestas, "conclusion_final": "Síntesis terminada."}

@app.post("/login")
def login(peticion: PeticionDebate): # Simplificado
    return {"status": "success"}
