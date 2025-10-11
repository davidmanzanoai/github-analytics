import anthropic
import os
import subprocess
import json

class GitHubRepoAgent:
    """
    Agente que analiza repositorios de GitHub usando Claude
    para responder preguntas sobre contribuidores, complejidad, documentación, etc.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Se requiere ANTHROPIC_API_KEY")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.conversation_history = []
        self.current_repo = None
        
    def obtener_info_repo(self, owner, repo):
        """
        Obtiene información básica del repositorio usando la API de GitHub
        """
        try:
            import requests
            
            # Información básica del repo
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {}
            
            # Si tienes un token de GitHub, úsalo para evitar límites
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            
            response = requests.get(repo_url, headers=headers)
            repo_data = response.json()
            
            # Obtener contribuidores
            contributors_url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
            contributors_response = requests.get(contributors_url, headers=headers)
            contributors_data = contributors_response.json()
            
            # Obtener commits recientes
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=100"
            commits_response = requests.get(commits_url, headers=headers)
            commits_data = commits_response.json()
            
            # Obtener estructura de archivos
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
            tree_response = requests.get(tree_url, headers=headers)
            tree_data = tree_response.json()
            
            return {
                "repo_info": repo_data,
                "contributors": contributors_data[:20],  # Top 20 contribuidores
                "recent_commits": commits_data[:50],  # Últimos 50 commits
                "file_tree": tree_data.get("tree", [])[:100]  # Primeros 100 archivos
            }
            
        except Exception as e:
            print(f"Advertencia: No se pudo obtener info del repo via API: {e}")
            return None
    
    def construir_contexto_repo(self, owner, repo, data):
        """
        Construye un contexto detallado del repositorio para Claude
        """
        if not data:
            return f"Repositorio: {owner}/{repo}\n(Información limitada disponible)"
        
        repo_info = data.get("repo_info", {})
        contributors = data.get("contributors", [])
        commits = data.get("recent_commits", [])
        files = data.get("file_tree", [])
        
        contexto = f"""# Análisis del Repositorio: {owner}/{repo}

## Información General
- Nombre: {repo_info.get('name', 'N/A')}
- Descripción: {repo_info.get('description', 'N/A')}
- Lenguaje principal: {repo_info.get('language', 'N/A')}
- Stars: {repo_info.get('stargazers_count', 0)}
- Forks: {repo_info.get('forks_count', 0)}
- Issues abiertos: {repo_info.get('open_issues_count', 0)}
- Tamaño: {repo_info.get('size', 0)} KB
- Creado: {repo_info.get('created_at', 'N/A')}
- Última actualización: {repo_info.get('updated_at', 'N/A')}

## Top Contribuidores (por número de commits)
"""
        
        for i, contributor in enumerate(contributors[:10], 1):
            contexto += f"{i}. {contributor.get('login', 'Unknown')} - {contributor.get('contributions', 0)} contribuciones\n"
        
        contexto += f"\n## Actividad Reciente ({len(commits)} commits analizados)\n"
        
        # Analizar frecuencia de commits
        if commits:
            dates = [c.get('commit', {}).get('author', {}).get('date', '') for c in commits if 'commit' in c]
            contexto += f"- Total de commits recientes analizados: {len(commits)}\n"
            contexto += f"- Primer commit del periodo: {dates[-1] if dates else 'N/A'}\n"
            contexto += f"- Último commit: {dates[0] if dates else 'N/A'}\n"
        
        contexto += f"\n## Estructura del Código ({len(files)} archivos principales)\n"
        
        # Analizar tipos de archivos
        extensiones = {}
        docs_files = []
        for file in files:
            if file.get('type') == 'blob':
                path = file.get('path', '')
                ext = path.split('.')[-1] if '.' in path else 'sin_extension'
                extensiones[ext] = extensiones.get(ext, 0) + 1
                
                # Detectar archivos de documentación
                lower_path = path.lower()
                if any(doc in lower_path for doc in ['readme', 'doc', 'guide', 'contributing', 'license']):
                    docs_files.append(path)
        
        contexto += "\nDistribución de archivos por tipo:\n"
        for ext, count in sorted(extensiones.items(), key=lambda x: x[1], reverse=True)[:10]:
            contexto += f"- .{ext}: {count} archivos\n"
        
        if docs_files:
            contexto += f"\n## Documentación encontrada ({len(docs_files)} archivos)\n"
            for doc in docs_files[:10]:
                contexto += f"- {doc}\n"
        
        return contexto
    
    def analizar_repo(self, owner, repo, pregunta):
        """
        Analiza un repositorio y responde una pregunta específica
        """
        
        # Obtener información del repositorio
        print(f"📊 Obteniendo información de {owner}/{repo}...")
        repo_data = self.obtener_info_repo(owner, repo)
        
        # Construir contexto
        contexto_repo = self.construir_contexto_repo(owner, repo, repo_data)
        
        # Guardar repo actual
        self.current_repo = (owner, repo, contexto_repo)
        
        # Sistema prompt mejorado
        system_prompt = f"""Eres un analista experto de repositorios de código en GitHub.

{contexto_repo}

Tu tarea es analizar este repositorio y responder preguntas de forma clara, concisa y basada en datos.
Proporciona estadísticas específicas, nombres concretos y análisis detallados cuando sea posible.
Si necesitas información que no está disponible en el contexto, indícalo claramente."""
        
        # Agregar pregunta al historial
        self.conversation_history = [{
            "role": "user",
            "content": pregunta
        }]
        
        try:
            print("🤖 Analizando con Claude...")
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=self.conversation_history
            )
            
            # Extraer respuesta
            respuesta = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    respuesta += block.text
            
            # Agregar al historial
            self.conversation_history.append({
                "role": "assistant",
                "content": respuesta
            })
            
            return respuesta
            
        except Exception as e:
            return f"❌ Error al analizar: {str(e)}"
    
    def pregunta_rapida(self, owner, repo, pregunta):
        """Pregunta rápida sin contexto previo"""
        return self.analizar_repo(owner, repo, pregunta)
    
    def conversacion_continua(self, pregunta):
        """Continúa la conversación sobre el mismo repo"""
        if not self.current_repo:
            return "⚠️ Primero inicia el análisis con analizar_repo()"
        
        owner, repo, contexto = self.current_repo
        
        self.conversation_history.append({
            "role": "user",
            "content": pregunta
        })
        
        system_prompt = f"""Eres un analista experto de repositorios de código.

{contexto}

Continúa la conversación sobre este repositorio respondiendo la nueva pregunta."""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=self.conversation_history
            )
            
            respuesta = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    respuesta += block.text
            
            self.conversation_history.append({
                "role": "assistant",
                "content": respuesta
            })
            
            return respuesta
            
        except Exception as e:
            return f"❌ Error: {str(e)}"


# ============= EJEMPLOS DE USO =============

def menu_interactivo():
    """Menú interactivo para usar el agente"""
    print("="*60)
    print("🤖 AGENTE DE ANÁLISIS DE REPOSITORIOS GITHUB")
    print("="*60)
    
    agente = GitHubRepoAgent()
    
    # Pedir datos del repositorio
    print("\n📁 Ingresa los datos del repositorio a analizar:")
    owner = input("Owner (ej: mozilla-ai): ").strip() or "mozilla-ai"
    repo = input("Repo (ej: lumigator): ").strip() or "lumigator"
    
    if not owner or not repo:
        print("❌ Debes ingresar owner y repo")
        return
    
    print("\n" + "="*60)
    print(f"Analizando: {owner}/{repo}")
    print("="*60 + "\n")
    
    # Menú de preguntas predefinidas
    preguntas_predefinidas = {
        "1": "¿Quién es la persona que más ha contribuido a este repositorio? Dame estadísticas.",
        "2": "Analiza la velocidad de desarrollo: ¿cuántos commits hay recientemente?",
        "3": "¿Cuál es el área más compleja del código basándote en la estructura de archivos?",
        "4": "Revisa la documentación del proyecto. ¿Está bien documentado?",
        "5": "Dame un resumen ejecutivo completo del repositorio.",
        "6": "¿Qué tecnologías y lenguajes se usan principalmente?",
        "0": "Hacer una pregunta personalizada"
    }
    
    while True:
        print("\n📋 OPCIONES:")
        for key, pregunta in preguntas_predefinidas.items():
            print(f"  {key}. {pregunta}")
        
        opcion = input("\nElige una opción (o 'q' para salir): ").strip()
        
        if opcion.lower() == 'q':
            print("\n👋 ¡Hasta luego!")
            break
        
        if opcion == "0":
            pregunta_custom = input("\n💬 Tu pregunta: ").strip()
            if not pregunta_custom:
                continue
            pregunta = pregunta_custom
        elif opcion in preguntas_predefinidas:
            pregunta = preguntas_predefinidas[opcion]
        else:
            print("❌ Opción inválida")
            continue
        
        print(f"\n🔍 Pregunta: {pregunta}\n")
        print("⏳ Analizando...\n")
        
        if len(agente.conversation_history) == 0:
            respuesta = agente.analizar_repo(owner, repo, pregunta)
        else:
            respuesta = agente.conversacion_continua(pregunta)
        
        print("="*60)
        print("📊 RESPUESTA:")
        print("="*60)
        print(respuesta)
        print("="*60)


if __name__ == "__main__":
    """
    SETUP RÁPIDO:
    
    1. Instala dependencias:
       pip install anthropic requests
    
    2. Configura tu API key de Anthropic:
       export ANTHROPIC_API_KEY='tu-api-key'
    
    3. (Opcional) Token de GitHub para más límites de API:
       export GITHUB_TOKEN='tu-github-token'
       
    4. Ejecuta:
       python github_agent.py
    """
    
    try:
        menu_interactivo()
    except KeyboardInterrupt:
        print("\n\n👋 Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")