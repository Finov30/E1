import requests
import json
import time
import sys
from typing import Dict, Any

def test_route(method: str, url: str, data: Dict[Any, Any] = None, files: Dict = None, expected_status: int = 200) -> bool:
    try:
        if method.upper() == 'GET':
            response = requests.get(url)
        elif method.upper() == 'POST':
            if files:
                response = requests.post(url, files=files)
            else:
                response = requests.post(url, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url)
        else:
            print(f"Méthode non supportée: {method}")
            return False

        if response.status_code == expected_status:
            print(f"✅ {method} {url} - Success")
            return True
        else:
            print(f"❌ {method} {url} - Failed (Status: {response.status_code}, Expected: {expected_status})")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ {method} {url} - Error: {str(e)}")
        return False

def run_tests(base_url: str = "http://localhost:8000") -> bool:
    print("\n🔍 Démarrage des tests des routes...")
    all_tests_passed = True
    created_user_id = None
    
    # Test data
    user_data = {
        "name": "Test User",
        "username": "@testuser",
        "password": "testpassword123"
    }
    
    address_data = {
        "street": "123 Test Street",
        "zipcode": "12345",
        "country": "France"
    }

    # Liste des tests à effectuer
    tests = [
        # Test de base
        ("GET", "/", None, None, 200),
        
        # Test création utilisateur avec adresse
        ("POST", "/users-with-address", {"user_data": user_data, "address_data": address_data}, None, 200),
        
        # Test scraping
        ("POST", "/scrape", None, None, 200),
        
        # Test upload CSV
        ("POST", "/upload-csv", None, {
            'file': ('sample_users.csv', open('sample_users.csv', 'rb'), 'text/csv')
        }, 200),
        
        # Test des fonctionnalités avancées
        ("POST", "/fetch-external-users", None, None, 200),
        ("POST", "/extract-from-faker-db", {"num_users": 2}, None, 200),
    ]

    # Exécution des tests initiaux
    for method, endpoint, data, files, expected_status in tests:
        success = test_route(method, f"{base_url}{endpoint}", data, files, expected_status)
        if not success:
            all_tests_passed = False

    # Test de lecture des utilisateurs et adresses
    print("\n🔍 Test de lecture des données...")
    response = requests.get(f"{base_url}/")
    if response.status_code == 200:
        users = response.json()
        if users:
            created_user_id = users[0].get('id')
            print(f"✅ Utilisateur trouvé avec ID: {created_user_id}")
            
            # Test de lecture spécifique
            tests_with_id = [
                ("GET", f"/users/{created_user_id}", None, None, 200),
                ("GET", f"/addresses/{created_user_id}", None, None, 200),
            ]
            
            # Test des routes de lecture
            for method, endpoint, data, files, expected_status in tests_with_id:
                success = test_route(method, f"{base_url}{endpoint}", data, files, expected_status)
                if not success:
                    all_tests_passed = False
            
            # Test de suppression
            print("\n🗑️ Test de suppression...")
            delete_tests = [
                ("DELETE", f"/addresses/{created_user_id}", None, None, 200),
                ("DELETE", f"/users/{created_user_id}", None, None, 200),
            ]
            
            # Test des routes de suppression
            for method, endpoint, data, files, expected_status in delete_tests:
                success = test_route(method, f"{base_url}{endpoint}", data, files, expected_status)
                if not success:
                    all_tests_passed = False
                    
            # Vérification que l'utilisateur a bien été supprimé
            response = requests.get(f"{base_url}/users/{created_user_id}")
            if response.status_code == 404:
                print("✅ Vérification de la suppression réussie")
            else:
                print("❌ L'utilisateur existe toujours après suppression")
                all_tests_passed = False
        else:
            print("❌ Aucun utilisateur trouvé pour les tests de suppression")
            all_tests_passed = False
    else:
        print("❌ Impossible de récupérer la liste des utilisateurs")
        all_tests_passed = False

    # Résumé des tests
    print("\n📊 Résumé des tests:")
    if all_tests_passed:
        print("✅ Tous les tests ont réussi!")
    else:
        print("❌ Certains tests ont échoué")

    return all_tests_passed

if __name__ == "__main__":
    print("⏳ Attente du démarrage de l'application...")
    time.sleep(10)  # Attendre que l'application démarre
    
    max_retries = 5
    for i in range(max_retries):
        try:
            if run_tests():
                sys.exit(0)
            else:
                if i < max_retries - 1:
                    print(f"\n🔄 Tentative {i+1}/{max_retries} échouée. Nouvelle tentative dans 5 secondes...")
                    time.sleep(5)
                else:
                    print("\n❌ Échec des tests après plusieurs tentatives")
                    sys.exit(1)
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                print(f"\n🔄 Serveur non disponible. Tentative {i+1}/{max_retries}. Nouvelle tentative dans 5 secondes...")
                time.sleep(5)
            else:
                print("\n❌ Impossible de se connecter au serveur après plusieurs tentatives")
                sys.exit(1) 