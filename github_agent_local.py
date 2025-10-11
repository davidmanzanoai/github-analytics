import requests
import os
from datetime import datetime
from collections import Counter, defaultdict
import json

class GitHubAnalyzer:
    """
    Analizador de repositorios GitHub que NO requiere API de Anthropic
    Todo el análisis se hace localmente con lógica Python
    """
    
    def __init__(self, github_token=None):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.headers = {}
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        
        self.cache = {}
    
    def obtener_datos_repo(self, owner, repo):
        """Obtiene todos los datos necesarios del repositorio"""
        print(f"📥 Descargando datos de {owner}/{repo}...")
        
        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        try:
            # Información básica
            print("  ⏳ Info del repositorio...")
            repo_info = self._get_json(base_url)
            
            # Contribuidores
            print("  ⏳ Contribuidores...")
            contributors = self._get_json(f"{base_url}/contributors?per_page=100")
            
            # Commits recientes
            print("  ⏳ Commits recientes...")
            commits = self._get_json(f"{base_url}/commits?per_page=100")
            
            # Árbol de archivos
            print("  ⏳ Estructura de archivos...")
            default_branch = repo_info.get('default_branch', 'main')
            tree = self._get_json(f"{base_url}/git/trees/{default_branch}?recursive=1")
            
            # Issues y PRs
            print("  ⏳ Issues y Pull Requests...")
            issues = self._get_json(f"{base_url}/issues?state=all&per_page=100")
            
            # Lenguajes
            print("  ⏳ Lenguajes...")
            languages = self._get_json(f"{base_url}/languages")
            
            print("✅ Datos descargados correctamente\n")
            
            return {
                'repo': repo_info,
                'contributors': contributors,
                'commits': commits,
                'tree': tree.get('tree', []) if isinstance(tree, dict) else [],
                'issues': issues,
                'languages': languages
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo datos: {e}")
            return None
    
    def _get_json(self, url):
        """Helper para hacer requests a GitHub API"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Error en {url}: {e}")
            return []
    
    def quien_mas_contribuye(self, data):
        """Analiza quién es el mayor contribuidor"""
        print("🏆 PRINCIPAL CONTRIBUIDOR")
        print("="*60)
        
        contributors = data.get('contributors', [])
        if not contributors:
            print("❌ No se encontraron contribuidores")
            return
        
        # Top 10 contribuidores
        print(f"\n📊 Top 10 Contribuidores (de {len(contributors)} totales):\n")
        for i, contrib in enumerate(contributors[:10], 1):
            login = contrib.get('login', 'Unknown')
            contributions = contrib.get('contributions', 0)
            print(f"{i:2}. {login:20} - {contributions:5} contribuciones")
        
        # Estadísticas del top 1
        top = contributors[0]
        total_contributions = sum(c.get('contributions', 0) for c in contributors)
        percentage = (top.get('contributions', 0) / total_contributions * 100) if total_contributions > 0 else 0
        
        print(f"\n🥇 Ganador: {top.get('login')}")
        print(f"   • Contribuciones: {top.get('contributions')}")
        print(f"   • Porcentaje del total: {percentage:.1f}%")
        print(f"   • Perfil: https://github.com/{top.get('login')}")
        print("="*60 + "\n")
    
    def velocidad_desarrollo(self, data):
        """Analiza la velocidad de desarrollo"""
        print("⚡ VELOCIDAD DE DESARROLLO")
        print("="*60)
        
        commits = data.get('commits', [])
        repo = data.get('repo', {})
        
        if not commits:
            print("❌ No se encontraron commits")
            return
        
        # Analizar fechas
        dates = []
        authors = []
        for commit in commits:
            commit_data = commit.get('commit', {})
            author_info = commit_data.get('author', {})
            date_str = author_info.get('date')
            
            if date_str:
                dates.append(datetime.fromisoformat(date_str.replace('Z', '+00:00')))
                authors.append(author_info.get('name', 'Unknown'))
        
        if not dates:
            print("❌ No se pudieron procesar las fechas")
            return
        
        # Estadísticas temporales
        dates.sort()
        primer_commit = dates[0]
        ultimo_commit = dates[-1]
        dias_transcurridos = (ultimo_commit - primer_commit).days
        
        print(f"\n📅 Periodo analizado:")
        print(f"   • Primer commit: {primer_commit.strftime('%Y-%m-%d %H:%M')}")
        print(f"   • Último commit: {ultimo_commit.strftime('%Y-%m-%d %H:%M')}")
        print(f"   • Días transcurridos: {dias_transcurridos}")
        
        print(f"\n📈 Métricas:")
        print(f"   • Total de commits (últimos 100): {len(commits)}")
        print(f"   • Commits por día: {len(commits)/dias_transcurridos:.2f}" if dias_transcurridos > 0 else "   • N/A")
        print(f"   • Commits por semana: {len(commits)/dias_transcurridos*7:.1f}" if dias_transcurridos > 0 else "   • N/A")
        
        # Autores únicos
        unique_authors = len(set(authors))
        print(f"   • Autores activos: {unique_authors}")
        
        # Repo info
        print(f"\n📊 Estado general del repositorio:")
        print(f"   • Stars: {repo.get('stargazers_count', 0)}")
        print(f"   • Forks: {repo.get('forks_count', 0)}")
        print(f"   • Watchers: {repo.get('watchers_count', 0)}")
        print(f"   • Issues abiertas: {repo.get('open_issues_count', 0)}")
        
        print("="*60 + "\n")
    
    def area_mas_compleja(self, data):
        """Identifica el área más compleja del código"""
        print("🧩 ÁREA MÁS COMPLEJA DEL CÓDIGO")
        print("="*60)
        
        tree = data.get('tree', [])
        if not tree:
            print("❌ No se pudo obtener la estructura de archivos")
            return
        
        # Analizar por directorio
        dir_stats = defaultdict(lambda: {'files': 0, 'total_size': 0, 'extensions': Counter()})
        
        for item in tree:
            if item.get('type') == 'blob':  # Es un archivo
                path = item.get('path', '')
                size = item.get('size', 0)
                
                # Obtener directorio
                parts = path.split('/')
                if len(parts) > 1:
                    directory = parts[0]
                else:
                    directory = '(raíz)'
                
                # Obtener extensión
                extension = path.split('.')[-1] if '.' in path else 'sin_ext'
                
                dir_stats[directory]['files'] += 1
                dir_stats[directory]['total_size'] += size
                dir_stats[directory]['extensions'][extension] += 1
        
        # Ordenar por número de archivos (indicador de complejidad)
        sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1]['files'], reverse=True)
        
        print(f"\n📁 Top 10 Directorios por número de archivos:\n")
        for i, (dirname, stats) in enumerate(sorted_dirs[:10], 1):
            size_mb = stats['total_size'] / (1024 * 1024)
            print(f"{i:2}. {dirname:30} - {stats['files']:4} archivos, {size_mb:.2f} MB")
        
        # El más complejo
        if sorted_dirs:
            most_complex = sorted_dirs[0]
            dirname, stats = most_complex
            
            print(f"\n🏆 Área más compleja: {dirname}")
            print(f"   • Archivos: {stats['files']}")
            print(f"   • Tamaño total: {stats['total_size'] / (1024 * 1024):.2f} MB")
            print(f"   • Tipos de archivo:")
            for ext, count in stats['extensions'].most_common(5):
                print(f"     - .{ext}: {count} archivos")
        
        print("="*60 + "\n")
    
    def revisar_documentacion(self, data):
        """Revisa la documentación del proyecto"""
        print("📚 ESTADO DE LA DOCUMENTACIÓN")
        print("="*60)
        
        tree = data.get('tree', [])
        repo = data.get('repo', {})
        
        # Buscar archivos de documentación
        doc_patterns = ['readme', 'contributing', 'license', 'changelog', 'docs/', 
                       'documentation', 'guide', 'tutorial', 'api', '.md']
        
        doc_files = []
        for item in tree:
            if item.get('type') == 'blob':
                path = item.get('path', '').lower()
                if any(pattern in path for pattern in doc_patterns):
                    doc_files.append({
                        'path': item.get('path'),
                        'size': item.get('size', 0)
                    })
        
        print(f"\n📄 Archivos de documentación encontrados: {len(doc_files)}\n")
        
        # Categorizar
        categories = {
            'README': [],
            'Guías de contribución': [],
            'Licencias': [],
            'Changelog': [],
            'Documentación API/Técnica': [],
            'Otros': []
        }
        
        for doc in doc_files:
            path = doc['path'].lower()
            if 'readme' in path:
                categories['README'].append(doc)
            elif 'contributing' in path or 'contribute' in path:
                categories['Guías de contribución'].append(doc)
            elif 'license' in path:
                categories['Licencias'].append(doc)
            elif 'changelog' in path or 'history' in path:
                categories['Changelog'].append(doc)
            elif 'docs/' in path or 'api' in path or 'guide' in path:
                categories['Documentación API/Técnica'].append(doc)
            else:
                categories['Otros'].append(doc)
        
        for category, files in categories.items():
            if files:
                print(f"📌 {category}: {len(files)} archivo(s)")
                for f in files[:3]:  # Mostrar máximo 3 por categoría
                    size_kb = f['size'] / 1024
                    print(f"   • {f['path']} ({size_kb:.1f} KB)")
                if len(files) > 3:
                    print(f"   ... y {len(files)-3} más")
        
        # Evaluación
        print(f"\n📊 Evaluación:")
        score = 0
        if categories['README']:
            print("   ✅ Tiene README")
            score += 2
        else:
            print("   ❌ Falta README")
        
        if categories['Guías de contribución']:
            print("   ✅ Tiene guía de contribución")
            score += 1
        
        if categories['Licencias']:
            print("   ✅ Tiene licencia")
            score += 1
        
        if len(categories['Documentación API/Técnica']) > 3:
            print("   ✅ Buena documentación técnica")
            score += 2
        elif categories['Documentación API/Técnica']:
            print("   ⚠️  Documentación técnica limitada")
            score += 1
        
        print(f"\n🎯 Puntuación de documentación: {score}/6")
        
        if repo.get('description'):
            print(f"\n💬 Descripción del repo: {repo.get('description')}")
        
        print("="*60 + "\n")
    
    def resumen_ejecutivo(self, data):
        """Genera un resumen ejecutivo completo"""
        print("📋 RESUMEN EJECUTIVO")
        print("="*60)
        
        repo = data.get('repo', {})
        contributors = data.get('contributors', [])
        languages = data.get('languages', {})
        commits = data.get('commits', [])
        
        print(f"\n🏷️  Nombre: {repo.get('full_name', 'N/A')}")
        if repo.get('description'):
            print(f"📝 Descripción: {repo.get('description')}")
        
        print(f"\n📊 Métricas clave:")
        print(f"   • ⭐ Stars: {repo.get('stargazers_count', 0):,}")
        print(f"   • 🔱 Forks: {repo.get('forks_count', 0):,}")
        print(f"   • 👀 Watchers: {repo.get('watchers_count', 0):,}")
        print(f"   • 🐛 Issues abiertas: {repo.get('open_issues_count', 0):,}")
        print(f"   • 📦 Tamaño: {repo.get('size', 0) / 1024:.1f} MB")
        
        print(f"\n👥 Comunidad:")
        print(f"   • Contribuidores: {len(contributors)}")
        if contributors:
            top3 = ', '.join([c.get('login', 'N/A') for c in contributors[:3]])
            print(f"   • Top 3: {top3}")
        
        print(f"\n💻 Tecnologías:")
        if languages:
            total = sum(languages.values())
            for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]:
                percentage = (bytes_count / total * 100) if total > 0 else 0
                print(f"   • {lang}: {percentage:.1f}%")
        
        print(f"\n📅 Actividad:")
        print(f"   • Creado: {repo.get('created_at', 'N/A')[:10]}")
        print(f"   • Última actualización: {repo.get('updated_at', 'N/A')[:10]}")
        if commits:
            print(f"   • Commits recientes analizados: {len(commits)}")
        
        print(f"\n🔗 Enlaces:")
        print(f"   • Repo: {repo.get('html_url', 'N/A')}")
        if repo.get('homepage'):
            print(f"   • Web: {repo.get('homepage')}")
        
        print("="*60 + "\n")
    
    def analizar_completo(self, owner, repo):
        """Realiza un análisis completo del repositorio"""
        print("\n" + "="*60)
        print(f"🔍 ANÁLISIS COMPLETO: {owner}/{repo}")
        print("="*60 + "\n")
        
        data = self.obtener_datos_repo(owner, repo)
        if not data:
            print("❌ No se pudo obtener los datos del repositorio")
            return
        
        # Realizar todos los análisis
        self.resumen_ejecutivo(data)
        self.quien_mas_contribuye(data)
        self.velocidad_desarrollo(data)
        self.area_mas_compleja(data)
        self.revisar_documentacion(data)
        
        print("✅ Análisis completado")


def menu_interactivo():
    """Menú interactivo"""
    print("="*60)
    print("🤖 ANALIZADOR DE REPOSITORIOS GITHUB (100% GRATUITO)")
    print("="*60)
    print("\n✨ No requiere API de Anthropic - Todo local")
    
    analyzer = GitHubAnalyzer()
    
    print("\n📁 Ingresa el repositorio a analizar:")
    owner = input("Owner (ej: mozilla-ai): ").strip() or "mozilla-ai"
    repo = input("Repo (ej: lumigator): ").strip() or "lumigator"
    
    if not owner or not repo:
        print("❌ Debes ingresar owner y repo")
        return
    
    # Obtener datos una sola vez
    data = analyzer.obtener_datos_repo(owner, repo)
    if not data:
        return
    
    while True:
        print("\n" + "="*60)
        print("📋 OPCIONES DE ANÁLISIS:")
        print("="*60)
        print("1. 🏆 ¿Quién más ha contribuido?")
        print("2. ⚡ Velocidad de desarrollo")
        print("3. 🧩 Área más compleja del código")
        print("4. 📚 Revisar documentación")
        print("5. 📋 Resumen ejecutivo completo")
        print("6. 🔄 Cambiar de repositorio")
        print("0. 👋 Salir")
        
        opcion = input("\nElige una opción: ").strip()
        
        if opcion == '0':
            print("\n👋 ¡Hasta luego!")
            break
        elif opcion == '1':
            analyzer.quien_mas_contribuye(data)
        elif opcion == '2':
            analyzer.velocidad_desarrollo(data)
        elif opcion == '3':
            analyzer.area_mas_compleja(data)
        elif opcion == '4':
            analyzer.revisar_documentacion(data)
        elif opcion == '5':
            analyzer.resumen_ejecutivo(data)
        elif opcion == '6':
            menu_interactivo()
            return
        else:
            print("❌ Opción inválida")
        
        input("\n⏎ Presiona Enter para continuar...")


if __name__ == "__main__":
    """
    SETUP ULTRA-RÁPIDO (100% GRATUITO):
    
    1. Instala una sola dependencia:
       pip install requests
    
    2. Ejecuta:
       python github_agent.py
    
    ¡Eso es todo! No necesitas ninguna API key de pago.
    
    OPCIONAL - Más límite de requests:
       export GITHUB_TOKEN='tu-token-de-github'
       (Obtén uno gratis en: https://github.com/settings/tokens)
    """
    
    try:
        menu_interactivo()
    except KeyboardInterrupt:
        print("\n\n👋 Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")