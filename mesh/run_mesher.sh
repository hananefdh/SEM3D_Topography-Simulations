#!/bin/bash
#SBATCH --job-name=sem3d_mesher
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=mesher_%j.out
#SBATCH --error=mesher_%j.err

set -Eeuo pipefail

MESHER="/gpfs/users/fidahh/build2/openacc-stable/MESH/mesher"
INPUT="templates/mesh.input"

if [[ ! -x "$MESHER" ]]; then
    echo "Erreur : exécutable Mesher introuvable : $MESHER" >&2
    exit 1
fi

if [[ ! -f "$INPUT" ]]; then
    echo "Erreur : fichier d'entrée introuvable : $INPUT" >&2
    exit 1
fi

# Transmettre les paramètres du fichier au Mesher
"$MESHER" < "$INPUT"

echo "Mesher terminé."

