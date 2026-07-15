import os
import sys
import asyncio
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.search.infrastructure.factories import get_search_engine
from apps.authentication.models import Tag

async def seed_documents():
    engine = get_search_engine()
    print(f"Utilisation du moteur de recherche : {engine.__class__.__name__}")
    
    sample_docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_docs")
    
    if not os.path.exists(sample_docs_dir):
        print(f"Erreur: Le dossier {sample_docs_dir} n'existe pas.")
        return

    documents = [
        {
            "filename": "rapport_maintenance_ligne_a.md",
            "tags": ["maintenance", "ligne-a"]
        },
        {
            "filename": "fiche_securite_solvants.md",
            "tags": ["sécurité", "confidentiel"]
        },
        {
            "filename": "procedure_qualite.md",
            "tags": ["qualité", "procédure"]
        }
    ]

    for doc in documents:
        filepath = os.path.join(sample_docs_dir, doc["filename"])
        if not os.path.exists(filepath):
            print(f"Fichier introuvable: {filepath}")
            continue

        print(f"Upload de {doc['filename']} avec les tags {doc['tags']}...")
        with open(filepath, "rb") as f:
            file_bytes = f.read()

        try:
            # Upload via le moteur de recherche
            result = await engine.upload(file_bytes=file_bytes, filename=doc["filename"], tags=doc["tags"])
            print(f"[SUCCES] Document ID = {result.document_id}")
            
            # S'assurer que les tags existent en base de données pour le frontend
            for tag_name in doc["tags"]:
                await Tag.objects.aget_or_create(name=tag_name)
                
        except Exception as e:
            print(f"[ERREUR] lors de l'upload de {doc['filename']}: {e}")

if __name__ == "__main__":
    asyncio.run(seed_documents())
    print("\nTerminé ! Vous pouvez maintenant tester la recherche sur DocSight.")
