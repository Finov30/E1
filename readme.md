# 1. Arrêter et nettoyer tous les conteneurs et volumes existants
docker-compose down --volumes --remove-orphans

# 2. Supprimer tous les réseaux non utilisés
docker network prune -f

# 3. Créer le réseau app-network
docker network create app-network

# 4. Démarrer les services
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up --build